from lyrebird.log import get_logger
from .server import serve, publish_init_status
from lyrebird.base_server import ProcessServer

logger = get_logger()


class ExtraMockServer(ProcessServer):

    def run(self, msg_queue, config, log_queue, *args, **kwargs):
        import os
        print(f'9999Server start on {os.getpid()}')
        # import signal
        # signal.signal(signal.SIGINT, signal.SIG_IGN)
        publish_init_status(msg_queue, 'READY')
        serve(msg_queue, config, log_queue, *args, **kwargs)
