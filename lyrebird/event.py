"""
Event bus

Worked as a backgrund thread
Run events handler and background task worker
"""
from queue import Queue
from multiprocessing import Manager, Process, Queue
from concurrent.futures import ThreadPoolExecutor
import traceback
import inspect
import uuid
import time
import copy
import types
from lyrebird.base_server import ThreadServer, ProcessServer, service_msg_queue
from lyrebird import application
from lyrebird.mock import context
from lyrebird import log
import copy
import json
import importlib


logger = log.get_logger()


application_white_map = {
    'config',
    '_cm'
}


context_white_map = {
    'application.data_manager.activated_data',
    'application.data_manager.activated_group'
}


class CheckerApplicationInfo(dict):

    def __init__(self, data=None, white_map={}):
        super().__init__()
        for path in white_map:
            value = self._get_value_from_path(data, path)
            if value is not None:
                self._set_value_to_path(path, value)

    def _get_value_from_path(self, data, path):
        keys = path.split('.')
        value = data
        for key in keys:
            value = getattr(value, key)
            if value is None:
                return None
        return value

    def _set_value_to_path(self, path, value):
        keys = path.split('.')
        current_dict = self
        for key in keys[:-1]:
            if key not in current_dict:
                current_dict[key] = CheckerApplicationInfo()
            current_dict = current_dict[key]
        current_dict[keys[-1]] = value

    
    def __getattr__(self, item):
        value = self
        for key in item.split('.'):
            value = value.get(key)
            if value is None:
                break
        return value

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        del self[item]


class InvalidMessage(Exception):
    pass


class Event:
    """
    Event bus inner class
    """

    def __init__(self, event_id, channel, message):
        self.id = event_id
        self.channel = channel
        self.message = message


def import_func_from_file(filepath, func_name):
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, func_name)
    return func


def get_func_from_obj(obj, method_name):
    return getattr(obj, method_name)


def get_callback_func(func_ori, func_name):
    if isinstance(func_ori, str):
        return import_func_from_file(func_ori, func_name)
    elif isinstance(func_ori, object):
        return get_func_from_obj(func_ori, func_name)
    else:
        logger.error(f'The source type of method {func_name} is invalid, exception method source: {func_ori}')


class CustomExecuteServer(ProcessServer):
    def __init__(self):
        super().__init__()
    
    def start(self, process_queue=None, process_namespace=None, publish_queue=None):
        if self.running:
            return

        global service_msg_queue
        if service_msg_queue is None:
            service_msg_queue = application.sync_manager.Queue()
        config = application.config.raw()
        logger_queue = application.server['log'].queue
        self.server_process = Process(group=None, target=self.run,
                                      args=[service_msg_queue, config, logger_queue, process_queue, process_namespace, publish_queue, self.args],
                                      kwargs=self.kwargs,
                                      daemon=True)
        self.server_process.start()
        self.running = True
    
    def run(self, msg_queue, config, log_queue, process_queue, process_namespace, publish_queue, *args, **kwargs):
        def monkey_path_publish(self, channel, message, publish_queue = publish_queue, *args, **kwargs):
            if channel == 'notice':
                self.check_notice(message)
            event_id = str(uuid.uuid4())

            # Make sure event is dict
            if not isinstance(message, dict):
                # Plugins send a array list as message, then set this message to raw property
                _msg = {'raw': message}
                message = _msg
            
            message_value = message.get('message', 'No message')
            if not isinstance(message_value, str):
                raise InvalidMessage('Value of key "message" must be a string.')

            message['channel'] = channel
            message['id'] = event_id
            message['timestamp'] = round(time.time(), 3)

            # Add event sender
            stack = inspect.stack()
            script_path = stack[2].filename
            script_name = script_path[script_path.rfind('/') + 1:]
            function_name = stack[2].function
            sender_dict = {
                "file": script_name,
                "function": function_name
            }
            message['sender'] = sender_dict

            publish_queue.put((event_id, channel, message, args, kwargs))

        def monkey_path_issue(self, title, message, publish_queue = publish_queue):
            notice = {
                "title": title,
                "message": message
            }
            self.check_notice(notice)

            event_id = str(uuid.uuid4())
            channel = 'notice'
            message = notice

            # Make sure event is dict
            if not isinstance(message, dict):
                # Plugins send a array list as message, then set this message to raw property
                _msg = {'raw': message}
                message = _msg
            
            message_value = message.get('message', 'No message')
            if not isinstance(message_value, str):
                raise InvalidMessage('Value of key "message" must be a string.')

            message['channel'] = channel
            message['id'] = event_id
            message['timestamp'] = round(time.time(), 3)

            # Add event sender
            stack = inspect.stack()
            script_path = stack[2].filename
            script_name = script_path[script_path.rfind('/') + 1:]
            function_name = stack[2].function
            sender_dict = {
                "file": script_name,
                "function": function_name
            }
            message['sender'] = sender_dict
            publish_queue.put((event_id, channel, message, args, kwargs))
        import os
        print(f'EventServer start on {os.getpid()}')      
        log.init(config, log_queue)
        self.running = True
        checker_event_server = EventServer(True)
        checker_event_server.event_queue = msg_queue
        checker_event_server.__class__.publish = monkey_path_publish
        import lyrebird
        from lyrebird import event
        lyrebird.application = process_namespace.application
        lyrebird.application.config = process_namespace.application._cm.config
        lyrebird.context = process_namespace.context
        lyrebird.application['server'] = CheckerApplicationInfo()
        lyrebird.application.server['event'] = checker_event_server
        event.__class__.publish = monkey_path_publish
        event.__class__.issue = monkey_path_issue
        # lyrebird.application.server['event'].event_queue = msg_queue

        while self.running:
            try:
                func_ori, func_name, callback_args, callback_kwargs = process_queue.get()
                callback_fn = get_callback_func(func_ori, func_name)
                callback_fn(*callback_args, **callback_kwargs)
            except Exception:
                traceback.print_exc()


class PublishServer(ThreadServer):
    def __init__(self):
        super().__init__()
        self.publish_msg_queue = application.sync_manager.Queue()

    def run(self):
        while self.running:
            try:
                event_id, channel, message, args, kwargs = self.publish_msg_queue.get()
                application.server['event'].publish(channel, message, event_id=event_id, *args, **kwargs)
            except Exception:
                traceback.print_exc()


class EventServer(ThreadServer):

    def __init__(self, no_start = False):
        super().__init__()
        
        self.state = {}
        self.pubsub_channels = {}
        # channel name is 'any'. Linstening on all channel
        self.any_channel = []
        self.process_executor_queue = None
        self.event_queue = None
        self.broadcast_executor = None
        self.process_executor = None
        self.publish_server = None
        if not no_start:
            self.event_queue = application.sync_manager.Queue()
            self.process_executor_queue = application.sync_manager.Queue()
            self.broadcast_executor = ThreadPoolExecutor(thread_name_prefix='event-broadcast-')
            self.process_executor = CustomExecuteServer()
            self.publish_server = PublishServer()

    def broadcast_handler(self, func_info, event, args, kwargs, process_queue=None):
        """

        """
        callback_fn = func_info.get('func')
        is_process = func_info.get('process')

        # Check
        func_sig = inspect.signature(callback_fn)
        func_parameters = list(func_sig.parameters.values())
        if len(func_parameters) < 1 or func_parameters[0].default != inspect._empty:
            logger.error(f'Event callback function [{callback_fn.__name__}] need a argument for receiving event object')
            return

        # Append event content to args
        callback_args = []
        if 'raw' in event.message:
            callback_args.append(event.message['raw'])
        else:
            callback_args.append(event.message)
        # Add channel to kwargs
        callback_kwargs = {}
        if 'channel' in func_sig.parameters:
            callback_kwargs['channel'] = event.channel
        if 'event_id' in func_sig.parameters:
            callback_kwargs['event_id'] = event.id
        # Execute callback function
        try:
            if is_process and isinstance(callback_fn, types.FunctionType) and event.channel in ('flow', 'page', 'flow.request', 'urlscheme.page'):
                process_queue.put((
                    func_info.get('origin'),
                    func_info.get('name'),
                    callback_args,
                    callback_kwargs
                ))
            else:
                callback_fn(*callback_args, **callback_kwargs)
        except Exception:
            logger.error(f'Event callback function [{callback_fn.__name__}] error. {traceback.format_exc()}')

    def run(self):
        while self.running:
            try:
                e = self.event_queue.get()
                # Deep copy event for async event system
                e = copy.deepcopy(e)
                callback_fn_list = self.pubsub_channels.get(e.channel)
                if callback_fn_list:
                    for callback_fn, args, kwargs in callback_fn_list:
                        self.broadcast_executor.submit(self.broadcast_handler, callback_fn, e, args, kwargs, self.process_executor_queue)
                for callback_fn, args, kwargs in self.any_channel:
                    self.broadcast_executor.submit(self.broadcast_handler, callback_fn, e, args, kwargs)
            except Exception:
                # empty event
                traceback.print_exc()
    
    def start(self, *args, **kwargs):
        super().start(*args, **kwargs)
        print('process_executor start')
        self.publish_server.start()
        self.process_namespace = application.sync_manager.Namespace()
        self.process_namespace.application = CheckerApplicationInfo(application, application_white_map)
        self.process_namespace.context = CheckerApplicationInfo(context, context_white_map)
        self.process_namespace.queue = application.server['event'].event_queue
        self.process_executor.start(self.process_executor_queue, self.process_namespace, self.publish_server.publish_msg_queue)

    def stop(self):
        super().stop()
        self.process_executor.stop()
        self.publish('system', {'name': 'event.stop'})

    def _check_message_format(self, message):
        """
        Check if the message content is valid.
        Such as: 'message' value must be a string.
        Other check rules can be added.
        """
        # Check value type of key 'message'
        message_value = message.get('message', 'No message')
        if not isinstance(message_value, str):
            raise InvalidMessage('Value of key "message" must be a string.')

    def publish(self, channel, message, state=False, event_id=None, *args, **kwargs):
        """
        publish message

        if type of message is dict, set default event information:
            - channel
            - id
            - timestamp
            - sender: if was cantained in message, do not update

        if state is true, message will be kept as state

        """
        if not event_id:
            # Make event id
            event_id = str(uuid.uuid4())

            # Make sure event is dict
            if not isinstance(message, dict):
                # Plugins send a array list as message, then set this message to raw property
                _msg = {'raw': message}
                message = _msg
            
            self._check_message_format(message)

            message['channel'] = channel
            message['id'] = event_id
            message['timestamp'] = round(time.time(), 3)

            # Add event sender
            stack = inspect.stack()
            script_path = stack[2].filename
            script_name = script_path[script_path.rfind('/') + 1:]
            function_name = stack[2].function
            sender_dict = {
                "file": script_name,
                "function": function_name
            }
            message['sender'] = sender_dict

            self.event_queue.put(Event(event_id, channel, message))
        else:
            self.event_queue.put(Event(event_id, channel, message))

        # TODO Remove state and raw data
        if state:
            if 'raw' in message:
                self.state[channel] = message['raw']
            else:
                self.state[channel] = message

        # Send event to socket-io
        context.application.socket_io.emit('event', {'id': event_id, 'channel': channel})

        # Send report
        if application.reporter:
            application.reporter.report({
                'action': 'event',
                'channel': channel,
                'event': message
            })

        logger.debug(f'channel={channel} state={state}\nmessage:\n-----------\n{message}\n-----------\n')

    def subscribe(self, func_info, *args, **kwargs):
        """
        Subscribe channel with a callback function
        That function will be called when a new message was published into it's channel

        callback function kwargs:
            channel=None receive channel name
        """
        channel = func_info['channel']
        if 'process' not in func_info:
            func_info['process'] = True
        if channel == 'any':
            self.any_channel.append([func_info, args, kwargs])
        else:
            callback_fn_list = self.pubsub_channels.setdefault(channel, [])
            callback_fn_list.append([func_info, args, kwargs])

    def unsubscribe(self, target_func_info, *args, **kwargs):
        """
        Unsubscribe callback function from channel
        """
        channel = target_func_info['channel']
        if channel == 'any':
            for any_info, *_ in self.any_channel:
                if target_func_info['func'] == any_info['func']:
                    self.any_channel.remove([target_func_info, *_])
        else:
            callback_fn_list = self.pubsub_channels.get(channel)
            for callback_fn_info, *_ in callback_fn_list:
                if target_func_info['func'] == callback_fn_info['func']:
                    callback_fn_list.remove([target_func_info, *_])


class CustomEventReceiver:
    """
    Event Receiver

    Decorator for plugin developer
    Usage:
        event = CustomEventReceiver()

        @event('flow')
        def on_message(data):
            pass
    """

    def __init__(self):
        self.listeners = []

    def __call__(self, channel, object=False, *args, **kw):
        def func(origin_func):
            self.listeners.append(dict(channel=channel, func=origin_func, object=object))
            return origin_func
        return func

    def register(self, event_bus):
        for listener in self.listeners:
            event_bus.subscribe(listener['channel'], listener['func'])

    def unregister(self, event_bus):
        for listener in self.listeners:
            event_bus.unsubscribe(listener['channel'], listener['func'])

    def publish(self, channel, message, *args, **kwargs):
        application.server['event'].publish(channel, message, *args, **kwargs)

    def issue(self, title, message):
        notice = {
            "title": title,
            "message": message
        }
        application.server['event'].publish('notice', notice)
