from lyrebird import application
from .function_executor import FunctionExecutor


class FlowEditorHandler(FunctionExecutor):

    def __init__(self):
        self.on_request = application.on_request
        self.on_response = application.on_response
        self.on_request_upstream = application.on_request_upstream
        self.on_response_upstream = application.on_response_upstream

    def on_request_handler(self, handler_context):
        matched_funcs = FlowEditorHandler.get_matched_sorted_handler(self.on_request, handler_context.flow)
        if not matched_funcs:
            return

        self.script_executor(matched_funcs, handler_context.flow)
        handler_context.set_request_edited(handler_context.flow.get('keep_origin_request_body', False))
        handler_context.flow['request']['headers']['lyrebird_modified'] = 'modified'

    def on_request_upstream_handler(self, handler_context):
        matched_funcs = FlowEditorHandler.get_matched_sorted_handler(self.on_request_upstream, handler_context.flow)
        if not matched_funcs:
            return

        self.script_executor(matched_funcs, handler_context.flow)
        handler_context.set_request_edited()
        handler_context.flow['request']['headers']['lyrebird_modified'] = 'modified'

    def on_response_upstream_handler(self, handler_context):
        matched_funcs = FlowEditorHandler.get_matched_sorted_handler(self.on_response_upstream, handler_context.flow)
        if not matched_funcs:
            return

        if not handler_context.flow['response'].get('data'):
            handler_context.update_response_data2flow()

        self.script_executor(matched_funcs, handler_context.flow)
        handler_context.set_response_edited()
        handler_context.flow['response']['headers']['lyrebird_modified'] = 'modified'

    def on_response_handler(self, handler_context):
        matched_funcs = FlowEditorHandler.get_matched_sorted_handler(self.on_response, handler_context.flow)
        if not matched_funcs:
            return

        # Set default value for handler function
        if not handler_context.flow['response'].get('code'):
            handler_context.flow['response']['code'] = 200
        if not handler_context.flow['response'].get('headers'):
            handler_context.flow['response']['headers'] = {}
        if 'data' not in handler_context.flow['response']:
            if handler_context.response:
                handler_context.update_response_data2flow()
            else:
                handler_context.flow['response']['data'] = None

        self.script_executor(matched_funcs, handler_context.flow)
        handler_context.set_response_edited()
        handler_context.flow['response']['headers']['lyrebird_modified'] = 'modified'

    @staticmethod
    def script_executor(func_list, flow):
        application.encoders_decoders.decoder_handler(flow)
        FlowEditorHandler.func_handler(func_list, flow)
        application.encoders_decoders.encoder_handler(flow)
