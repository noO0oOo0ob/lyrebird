import re
import traceback
from lyrebird.log import get_logger
from lyrebird.utils import HookedDict
import numba

logger = get_logger()

def get_rank(f):
        return f['rank']

def func_handler(func_list:list, flow:HookedDict, handler_type='flow_editor'):
    for func_info in func_list:
        handler_fn = func_info['func']
        try:
            handler_fn(flow)
            # TODO: The flow is changed or not?
            action = {
                'id': handler_type,
                'name': func_info['name']
            }
            if flow.get('action'):
                flow['action'].append(action)
            else:
                flow['action'] = [action]
        except Exception:
            logger.error(traceback.format_exc())

def get_matched_sorted_handler(func_list:list, flow:HookedDict):
    matched_func = []
    if not isinstance(flow, HookedDict):
        flow = HookedDict(flow)
    for func in func_list:
        rules = func['rules']
        if not rules or _is_req_match_rule(rules, flow):
            matched_func.append(func)
    matched_sorted_func = sorted(matched_func, key = get_rank)
    return matched_sorted_func


@numba.jit(nopython = False, forceobj=True)
def _is_req_match_rule(rules:list, flow:HookedDict):
    for rule_key in rules:
        pattern = rules[rule_key]
        target = _get_rule_target(rule_key, flow)
        if not target or not re.search(pattern, target):
            return False
    return True

@numba.jit(nopython = False, forceobj=True)
def _get_rule_target(rule_key:list, flow:HookedDict):
    prop_keys = rule_key.split('.')
    result = flow
    for prop_key in prop_keys:
        result = result.get(prop_key)
        if not result:
            return None
    return result
