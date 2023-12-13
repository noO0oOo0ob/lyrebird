from copy import deepcopy
from lyrebird import application
from .function_executor import *


class EncoderDecoder():
    def __init__(self):
        self.encoder = application.encoder
        self.decoder = application.decoder

    def encoder_handler(self, flow, output=None):
        matched_funcs = get_matched_sorted_handler(self.encoder, flow)
        if output == None:
            func_handler(matched_funcs, flow, handler_type='encoder')
            return

        new_flow = deepcopy(flow)
        if not matched_funcs:
            output.update(new_flow)
            return

        func_handler(matched_funcs, new_flow, handler_type='encoder')
        output.update(new_flow)

    def decoder_handler(self, flow, output=None):
        matched_funcs = get_matched_sorted_handler(self.decoder, flow)
        if output == None:
            func_handler(matched_funcs, flow, handler_type='decoder')
            return

        new_flow = deepcopy(flow)
        if not matched_funcs:
            output.update(new_flow)
            return

        func_handler(matched_funcs, new_flow, handler_type='decoder')
        output.update(new_flow)
