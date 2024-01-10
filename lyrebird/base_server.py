"""
Base threading server class
"""

import inspect
from threading import Thread
from multiprocessing import Process, Manager, Queue
from lyrebird import application
from multiprocessing.managers import Namespace

service_msg_queue = None
# service_msg_queue = Queue()

application_white_map = {
    'config',
    '_cm'
}


context_white_map = {
    'application.data_manager.activated_data',
    'application.data_manager.activated_group'
}


def check_process_server_run_function_compatibility(function):
    # Check whether the run method is an old or new version by params.
    if len(inspect.signature(function).parameters) == 4 and list(inspect.signature(function).parameters.keys())[0] == 'async_obj':
        return True
    else:
        return False


def prepare_application_for_monkey_patch() -> Namespace:
    from lyrebird import application, context
    namespace = application.sync_manager.get_namespace()
    namespace.application = CheckerApplicationInfo(application, application_white_map)
    namespace.context = CheckerApplicationInfo(context, context_white_map)
    namespace.queue = application.server['event'].event_queue
    return namespace


def monkey_patch_application(async_obj, async_funcs=None):
    import lyrebird
    from lyrebird.event import EventServer
    from lyrebird import event

    msg_queue = async_obj['msg_queue']
    process_namespace = async_obj['process_namespace']
    
    lyrebird.application = process_namespace.application
    lyrebird.application.config = process_namespace.application._cm.config
    lyrebird.context = process_namespace.context

    if async_funcs:
        checker_event_server = EventServer(True)
        checker_event_server.event_queue = msg_queue
        lyrebird.application['server'] = CheckerApplicationInfo()
        lyrebird.application.server['event'] = checker_event_server
        checker_event_server.__class__.publish = async_funcs['publish']
        event.__class__.publish = async_funcs['publish']
        event.__class__.issue = async_funcs['issue']


def monkey_patch_publish(channel, message, publish_queue, *args, **kwargs):
    from lyrebird.event import EventServer
    from lyrebird.checker.event import CheckerEventHandler
    if channel == 'notice':
        CheckerEventHandler.check_notice(message)
    
    event_id, channel, message = EventServer.get_publish_message(channel, message)
    publish_queue.put((event_id, channel, message, args, kwargs))


def monkey_patch_issue(title, message, publish_queue, *args, **kwargs):
    from lyrebird.event import EventServer
    from lyrebird.checker.event import CheckerEventHandler
    notice = {
        "title": title,
        "message": message
    }
    CheckerEventHandler.check_notice(notice)

    event_id, channel, message = EventServer.get_publish_message('notice', notice)
    publish_queue.put((event_id, channel, message, args, kwargs))


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


class ProcessServer:
    def __init__(self):
        ProcessManager.add(self)
        self.server_process = None
        self.running = False
        self.name = None
        self.event_thread = None
        self.async_obj = {}
        self.args = []
        self.kwargs = {}

    def run(self, async_obj, config, *args, **kwargs):
        '''
        msg_queue
        message queue for process server and main process

        #1. Send event to main process,
        {
            "type": "event",
            "channel": "",
            "content": {}
        }

        #2. Send message to frontend
        support channel: msgSuccess msgInfo msgError
        {
            "type": "ws",
            "channel": "",
            "content": ""
        }

        config
        lyrebird config dict

        log_queue
        send log msg to logger process
        '''
        pass

    def start(self):
        if self.running:
            return
        
        from lyrebird.log import get_logger
        logger = get_logger()

        global service_msg_queue
        if service_msg_queue is None:
            service_msg_queue = application.sync_manager.get_multiprocessing_queue()
        config = application._cm.config
        logger_queue = application.server['log'].queue

        # run method has too many arguments. Merge the msg_queue, log_queue and so on into async_obj
        # This code is used for compatibility with older versions of the run method in the plugin
        # This code should be removed after all upgrades have been confirmed
        if check_process_server_run_function_compatibility(self.run):
            self.async_obj['logger_queue'] = logger_queue
            self.async_obj['msg_queue'] = service_msg_queue
            self.server_process = Process(group=None, target=self.run,
                                        args=[self.async_obj, config, self.args],
                                        kwargs=self.kwargs,
                                        daemon=True)
        else:
            logger.warning(f'The run method in {type(self).__name__} is an old parameter format that will be removed in the future')
            self.server_process = Process(group=None, target=self.run,
                                        args=[service_msg_queue, config, logger_queue, self.args],
                                        kwargs=self.kwargs,
                                        daemon=True)
        self.server_process.start()
        self.running = True

    def stop(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.join()
    
    def pre_stop(self):
        self.running = False


class ProcessManager:

    processes = []

    @staticmethod
    def add(process:ProcessServer, name:str=None):
        name = name if name else type(process).__name__
        ProcessManager.processes.append((name, process))
    
    @staticmethod
    def pre_stop():
        for _,process in ProcessManager.processes:
            process.pre_stop()

    @staticmethod
    def destory():
        for name, process in ProcessManager.processes:
            process.stop()


class ThreadServer:

    def __init__(self):
        self.server_thread = None
        self.running = False
        self.name = None

    def start(self, *args, **kwargs):
        if self.running:
            return
        self.running = True
        self.server_thread = Thread(target=self.run, name=self.name, args=args, kwargs=kwargs)
        self.server_thread.start()

    def stop(self):
        self.running = False
        if self.server_thread and self.server_thread.is_alive():
            print(self)
            self.server_thread.join()
        # TODO terminate self.server_thread
    
    def pre_stop(self):
        self.running = False

    def run(self):
        """
        Server main function
        """
        pass


class StaticServer:

    def start(self, *args, **kwargs):
        pass

    def stop(self):
        pass
    
    def pre_stop(self):
        pass


class MultiProcessServerMessageDispatcher(ThreadServer):

    def run(self):
        global service_msg_queue
        if service_msg_queue is None:
            service_msg_queue = application.sync_manager.get_multiprocessing_queue()
        emit = application.server['mock'].socket_io.emit
        publish = application.server['event'].publish

        while self.running:
            msg = service_msg_queue.get()
            if msg is None:
                break
            type = msg.get('type')
            if type == 'event':
                channel = msg.get('channel')
                event = msg.get('content')
                if channel and event:
                    publish(channel, event)
            elif type == 'ws':
                ws_channel = msg.get('channel')
                ws_msg = msg.get('content', '')
                if ws_channel:
                    emit(ws_channel, ws_msg)
            else:
                pass
