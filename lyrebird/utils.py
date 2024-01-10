import re
import os
import json
import math
import time
import uuid
import redis
import pickle
import socket
import tarfile
import requests
import datetime
import netifaces
import traceback
import hashlib
from pathlib import Path
from multiprocessing import shared_memory
from jinja2 import Template, StrictUndefined
from jinja2.exceptions import UndefinedError, TemplateSyntaxError
from contextlib import closing
from urllib.parse import unquote
from lyrebird.log import get_logger
from lyrebird.application import config

logger = get_logger()

REDIS_EXPIRE_TIME = 60*60*24


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def convert_size_to_byte(size_str: str):
    size_str = size_str.strip().upper()
    match = re.match(r'^(\d+\.?\d*)\s*([KMGTPEZY]?[B])$', size_str)
    if not match:
        logger.warning(f'Invalid size string: {size_str}')
        return
    size = float(match.group(1))
    unit = match.group(2)
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = size_name.index(unit)
    size_bytes = int(size * (1024 ** i))
    return size_bytes


def convert_time(duration):
    if duration < 1:
        return str(round(duration * 1000)) + 'ms'
    else:
        return str(round(duration, 2)) + 's'


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print(f'{method.__name__} execution time {(te-ts)*1000}')
        return result
    return timed


def is_port_in_use(port, host='127.0.0.1'):
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((host, int(port)))
        return True
    except socket.error:
        return False
    finally:
        if sock:
            sock.close()


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def get_ip():
    """
    Get local ip from socket connection

    :return: IP Addr string
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]


def get_interface_ipv4():
    ipv4_list = []
    interface_list = netifaces.interfaces()
    for interface_name in interface_list:
        if interface_name == 'lo0':
            continue
        interface_dict = netifaces.ifaddresses(interface_name)
        interface = interface_dict.get(netifaces.AF_INET)
        if not interface:
            continue
        for alias in interface:
            ipv4_list.append({
                'address': alias['addr'],
                # windows keyerror 'netmask'
                # https://github.com/Meituan-Dianping/lyrebird/issues/665
                'netmask': alias.get('netmask', ''),
                'interface': interface_name
            })
    return ipv4_list


def compress_tar(input_path, output_path, suffix=None):
    current_path = Path.cwd()
    input_path = Path(input_path).expanduser().absolute().resolve()
    output_path = Path(output_path).expanduser().absolute().resolve()
    output_file = f'{output_path}{suffix}' if suffix else output_path

    os.chdir(input_path)
    # If not chdir, the directory in the compressed file will start from the root directory
    tar = tarfile.open(output_file, 'w:gz')
    for root, dirs, files in os.walk(input_path):
        for f in files:
            tar.add(f, recursive=False)
    tar.close()
    os.chdir(current_path)
    return output_file


def decompress_tar(input_path, output_path=None):
    input_path = Path(input_path).expanduser().absolute().resolve()
    if not output_path:
        filename = input_path.stem if input_path.suffix else f'{input_path.name}-decompress'
        output_path = input_path.parent / filename

    tf = tarfile.open(str(input_path))
    tf.extractall(str(output_path))
    tf.close()
    return output_path


def download(link, input_path):
    resp = requests.get(link, stream=True)
    with open(input_path, 'wb') as f:
        for chunck in resp.iter_content():
            f.write(chunck)


def handle_jinja2_tojson_by_config(data):
    config_value_tojson_key = config.get('config.value.tojsonKey')
    data_with_tojson = data
    for tojson_key in config_value_tojson_key:

        # EXAMPLE
        # response_data = `"key1":"value1","key2":"{{config.get('model.id')}}","key3":"value3"`
        # target_match_data = `"{{config.get('model.id')}}"`
        # Divide target_match_data into three parts `"{{` and `config.get('model.id')` and `}}"`
        # In the second part, `model.id` is a matching rule from Lyrebird configuration
        # The final return response_data is `"key1":"value1","key2":{{config.get('model.id') | tojson}},"key3":"value3"`

        pattern = '[^:]*' + tojson_key + '[^,]*'
        # The format of the group is required
        pattern_group = '(' + pattern + ')'
        data_with_tojson = re.sub('("{{)'+pattern_group+'(}}")', r'{{\2 | tojson}}', data_with_tojson)
    return data_with_tojson


def handle_jinja2_keywords(data, params=None):
    '''
    Jinja2 will throw an exception when dealing with unexpected left brackets, but right brackets will not
    So only left brackets need to be handled

    Handle 3 kinds of unexpected left brackets:
    1. More than 2 big brackets              `{{{ }}}` `{{# #}}` `{{% %}}`
    2. Mismatched keyword                    `{{{` `{{#` `{{%`
    3. Unknown arguments between {{ and }}   `{{unknown}}`

    Convert unexpected brackets into presentable string in Jinja2, such as `var` -> `{{ 'var' }}`
    The unexpected left brackets above will be convert into:
    `{{#`          ->  `{{ '{{#' }}`
    `{{unknown}}`  ->  `{{ '{{' }}unknown{{ '}}' }}`
    '''

    keywords_pair = {
        '{{': '}}',
        '{%': '%}',
        '{#': '#}'
    }

    # split by multiple `{` followed by `{` or `#`` or `%`, such as `{{`, `{{{`, `{{{{`, `{#`, `{{#`
    # EXAMPLE
    # data = '{{ip}} {{ip {{{ip'
    # item_list = ['', '{{', 'ip}} ', '{{', 'ip ', '{{{', 'ip']
    item_list = re.split('({+[{|#|%])', data)
    if len(item_list) == 1:
        return data

    left_pattern_index = None
    for index, item in enumerate(item_list):
        if index % 2:
            # 1. Handle more than 2 big brackets
            if (len(item) > 2) or (item not in keywords_pair):
                item_list[index] = "{{ '%s' }}" % (item)
            else:
                left_pattern_index = index
            continue

        if left_pattern_index is None:
            continue

        left_pattern = item_list[left_pattern_index]
        left_pattern_index = None

        # 2. Handle mismatched keyword
        right_pattern = keywords_pair[left_pattern]
        if right_pattern not in item:
            item_list[index-1] = "{{ '%s' }}" % (item_list[index-1])
            continue

        # 3. Handle unknown arguments between {{ and }}
        if left_pattern == '{{':
            key_n_lefted = item.split('}}', 1)
            if len(key_n_lefted) != 2:
                continue
            key, _ = key_n_lefted
            key = key.strip()
            if [key for p in params if key.startswith(p)]:
                continue
            item_list[index-1] = "{{ '%s' }}" % (item_list[index-1])

    after_data = ''.join(item_list)
    return after_data


def render(data, enable_tojson=True):
    if not isinstance(data, str):
        logger.warning(f'Format error! Expected str, found {type(data)}')
        return

    params = {
        'config': config,
        'ip': config.get('ip'),
        'port': config.get('mock.port'),
        'today': datetime.date.today(),
        'now':  datetime.datetime.now()
    }

    if enable_tojson:
        data = handle_jinja2_tojson_by_config(data)

    # Jinja2 doc
    # undefined and UndefinedError https://jinja.palletsprojects.com/en/3.1.x/api/#undefined-types
    # TemplateSyntaxError https://jinja.palletsprojects.com/en/3.1.x/api/#jinja2.TemplateSyntaxError

    try:
        template_data = Template(data, keep_trailing_newline=True, undefined=StrictUndefined)
        data = template_data.render(params)
    except (UndefinedError, TemplateSyntaxError):
        data = handle_jinja2_keywords(data, params)
        template_data = Template(data, keep_trailing_newline=True)
        data = template_data.render(params)
    except Exception:
        logger.error(f'Format error!\n {traceback.format_exc()}')

    return data


def get_query_array(url):
    # query string to array, example:
    # a=1&b=2 ==> ['a', '1', 'b', '2']
    # a=&b=2 ==> ['a', '', 'b', '2']
    # a&b=2 ==> ['a', '', 'b', '2']
    query_array = []
    qs_index = url.find('?')
    if qs_index < 0:
        return query_array

    query_string = url[qs_index+1:]
    if not query_string:
        return query_array

    for k_v in query_string.split('&'):
        if not k_v:
            continue

        k_v_item = k_v.split('=')
        if len(k_v_item) >= 2:
            query_array.extend(k_v_item[:2])
        else:
            query_array.extend([k_v, ''])
    return query_array


def url_decode(decode_obj, decode_key):
    if not isinstance(decode_obj, (dict, list)):
        return
    if isinstance(decode_obj, dict) and decode_key not in decode_obj:
        return
    if isinstance(decode_obj, list) and (not isinstance(decode_key, int) or decode_key >= len(decode_obj)):
        return
    url_decode_for_list_or_dict(decode_obj, decode_key)


def url_decode_for_list_or_dict(decode_obj, decode_key):
    if isinstance(decode_obj[decode_key], str):
        decode_obj[decode_key] = unquote(decode_obj[decode_key])
    elif isinstance(decode_obj[decode_key], list):
        for idx, _ in enumerate(decode_obj[decode_key]):
            url_decode(decode_obj[decode_key], idx)
    elif isinstance(decode_obj[decode_key], dict):
        for key, _ in decode_obj[decode_key].items():
            url_decode(decode_obj[decode_key], key)


def flow_str_2_data(data_str):
    if not isinstance(data_str, str):
        return data_str
    try:
        return json.loads(data_str)
    except Exception:
        return data_str


def flow_data_2_str(data):
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False)


class CaseInsensitiveDict(dict):
    '''
    A dict data-structure that ignore key's case.
    Any read or write related operations will igonre key's case.

    Example:
    <key: 'abc'> & <key: 'ABC'> will be treated as the same key, only one exists in this dict.
    '''

    def __init__(self, raw_dict=None):
        self.__key_map = {}
        if raw_dict:
            for k, v in raw_dict.items():
                self.__setitem__(k, v)
    
    def __getstate__(self):
        return {
            'key_map': self.__key_map,
            'data': dict(self)
        }

    def __setstate__(self, state):
        self.__key_map = state['key_map']
        self.update(state['data'])

    def __get_real_key(self, key):
        return self.__key_map.get(key.lower(), key)

    def __set_real_key(self, real_key):
        if real_key.lower() not in self.__key_map:
            self.__key_map[real_key.lower()] = real_key

    def __pop_real_key(self, key):
        return self.__key_map.pop(key.lower())

    def __del_real_key(self, key):
        del self.__key_map[key.lower()]

    def __clear_key_map(self):
        self.__key_map.clear()

    def __setitem__(self, key, value):
        real_key = self.__get_real_key(key)
        self.__set_real_key(real_key)
        super(CaseInsensitiveDict, self).__setitem__(real_key, value)

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__get_real_key(key))

    def get(self, key, default=None):
        return super(CaseInsensitiveDict, self).get(self.__get_real_key(key), default)

    def __delitem__(self, key):
        real_key = self.__pop_real_key(key)
        return super(CaseInsensitiveDict, self).__delitem__(real_key)

    def __contains__(self, key):
        return key.lower() in self.__key_map

    def pop(self, key):
        real_key = self.__pop_real_key(key)
        return super(CaseInsensitiveDict, self).pop(real_key)

    def popitem(self):
        item = super(CaseInsensitiveDict, self).popitem()
        if item:
            self.__del_real_key(item[0])
        return item

    def clear(self):
        self.__clear_key_map()
        return super(CaseInsensitiveDict, self).clear()

    def update(self, __m=None, **kwargs) -> None:
        if __m:
            for k, v in __m.items():
                self.__setitem__(k, v)
        if kwargs:
            for k, v in kwargs.items():
                self.__setitem__(k, v)

    def __reduce__(self):
        return (self.__class__, (dict(self),))

class HookedDict(dict):
    '''
    Hook build-in dict to protect CaseInsensitiveDict data type.
    Only <headers> value is CaseInsensitiveDict at present.
    '''

    def __init__(self, raw_dict=None):
        if raw_dict:
            for k, v in raw_dict.items():
                if type(v) == dict:
                    if k.lower() == 'headers':
                        v = CaseInsensitiveDict(v)
                    else:
                        v = HookedDict(v)
                self.__setitem__(k, v)

    def __setitem__(self, __k, __v) -> None:
        if type(__v) == dict:
            if __k.lower() == 'headers':
                __v = CaseInsensitiveDict(__v)
            else:
                __v = HookedDict(__v)
        return super(HookedDict, self).__setitem__(__k, __v)

    def __reduce__(self):
        return (self.__class__, (dict(self),))



class TargetMatch:

    @staticmethod
    def is_match(target, pattern):
        if not TargetMatch._match_type(target, pattern):
            return False
        if type(target) == str:
            return TargetMatch._match_string(target, pattern)
        elif type(target) in [int, float]:
            return TargetMatch._match_numbers(target, pattern)
        elif type(target) == bool:
            return TargetMatch._match_boolean(target, pattern)
        elif type(target).__name__ == 'NoneType':
            return TargetMatch._match_null(target, pattern)
        else:
            logger.warning(f'Illegal match target type: {type(target)}')
            return False

    @staticmethod
    def _match_type(target, pattern):
        return isinstance(target, type(pattern))

    @staticmethod
    def _match_string(target, pattern):
        return True if re.search(pattern, target) else False

    @staticmethod
    def _match_numbers(target, pattern):
        return target == pattern

    @staticmethod
    def _match_boolean(target, pattern):
        return target == pattern

    @staticmethod
    def _match_null(target, pattern):
        return target == pattern


class JSONFormat:

    def json(self):
        prop_collection = {}
        props = dir(self)
        for prop in props:
            if prop.startswith('_'):
                continue
            prop_obj = getattr(self, prop)
            if isinstance(prop_obj, (str, int, bool, float)):
                prop_collection[prop] = prop_obj
            elif isinstance(prop_obj, datetime.datetime):
                prop_collection[prop] = prop_obj.timestamp()
        return prop_collection


class RedisManager:

    redis_dicts = set()

    @staticmethod
    def put(obj):
        RedisManager.redis_dicts.add(obj)

    @staticmethod
    def destory():
        for i in RedisManager.redis_dicts:
            i.destory()
        RedisManager.redis_dicts.clear()

    @staticmethod
    def serialize():
        return pickle.dumps(RedisManager.redis_dicts)

    @staticmethod
    def deserialize(data):
        RedisManager.redis_dicts = pickle.loads(data)


class RedisData:

    host = 'localhost'
    port = 6379
    db = 0

    def __init__(self, host=None, port=None, db=None, param_uuid=None):
        if not host:
            host = RedisData.host
        if not port:
            port = RedisData.port
        if not db:
            db = RedisData.db
        self.port = port
        self.host = host
        self.db = db
        if not param_uuid:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = param_uuid
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)
        RedisManager.put(self)

    def destory(self):
        self.redis.delete(self.uuid)
        self.redis.close()


    def __getstate__(self):
        return pickle.dumps({
            'uuid':self.uuid,
            'port':self.port,
            'host':self.host,
            'db':self.db
            })

    def __setstate__(self, state):
        data = pickle.loads(state)
        self.port = data['port']
        self.host = data['host']
        self.db = data['db']
        self.uuid = data['uuid']
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)


class RedisDict(RedisData):

    def __init__(self, host=None, port=None, db=None, param_uuid=None, data={}):
        super().__init__(host, port, db, param_uuid)
        for k in data.keys():
            self[k] = data[k]

    def __getitem__(self, key):
        value = self.redis.hget(self.uuid, key)
        if value is None:
            raise KeyError(key)
        return json.loads(value.decode())

    def __setitem__(self, key, value):
        self.redis.hset(self.uuid, key, json.dumps(value, ensure_ascii=False))
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def __delitem__(self, key):
        if not self.redis.hexists(self.uuid, key):
            raise KeyError(key)
        self.redis.hdel(self.uuid, key)
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def __contains__(self, key):
        return self.redis.hexists(self.uuid, key)

    def keys(self):
        return [key.decode() for key in self.redis.hkeys(self.uuid)]

    def values(self):
        return [json.loads(value.decode()) for value in self.redis.hgetall(self.uuid).values()]

    def items(self):
        return [(key.decode(), json.loads(value.decode())) for key, value in self.redis.hgetall(self.uuid).items()]

    def get(self, key, default=None):
        value = self.redis.hget(self.uuid, key)
        if value is None:
            return default
        return json.loads(value.decode())

    def update(self, data):
        for key, value in data.items():
            self[key] = value
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)
    
    def clear(self):
        self.redis.delete(self.uuid)

    def raw(self):
        return {key.decode(): json.loads(value.decode()) for key, value in self.redis.hgetall(self.uuid).items()}

    def __len__(self):
        return len(self.redis.hkeys(self.uuid))

    def __repr__(self):
        return repr(dict(self.items()))


class RedisList(RedisData):

    def __init__(self, host=None, port=None, db=None, param_uuid=None, data=[]):
        super().__init__(host, port, db, param_uuid)
        for item in data:
            self.append(item)

    def __getitem__(self, index):
        value = self.redis.lindex(self.uuid, index)
        if value is None:
            raise IndexError("list index out of range")
        return json.loads(value.decode())

    def __setitem__(self, index, value):
        self.redis.lset(self.uuid, index, json.dumps(value, ensure_ascii=False))
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def __delitem__(self, index):
        self.redis.lset(self.uuid, index, '__DELETED__')
        self.redis.lrem(self.uuid, 1, '__DELETED__')
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def __contains__(self, value):
        return self.redis.lrange(self.uuid, 0, -1).__contains__(json.dumps(value, ensure_ascii=False))

    def __len__(self):
        return self.redis.llen(self.uuid)

    def __repr__(self):
        return repr(self.redis.lrange(self.uuid, 0, -1))

    def append(self, value):
        self.redis.rpush(self.uuid, json.dumps(value, ensure_ascii=False))
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def extend(self, values):
        pipe = self.redis.pipeline()
        for value in values:
            pipe.rpush(self.uuid, json.dumps(value, ensure_ascii=False))
        pipe.execute()

    def insert(self, index, value):
        self.redis.linsert(self.uuid, 'BEFORE', json.dumps(self[index], ensure_ascii=False), json.dumps(value, ensure_ascii=False))

    def remove(self, value):
        self.redis.lrem(self.uuid, 1, json.dumps(value, ensure_ascii=False))

    def pop(self, index=-1):
        value = self[index]
        del self[index]
        return value

    def index(self, value, start=None, end=None):
        values = self.redis.lrange(self.uuid, start, end)
        try:
            return values.index(json.dumps(value, ensure_ascii=False))
        except ValueError:
            raise ValueError("list.index(x): x not in list")

    def count(self, value):
        return self.redis.lrange(self.uuid, 0, -1).count(json.dumps(value, ensure_ascii=False))

    def clear(self):
        self.redis.delete(self.uuid)
    
    def raw(self):
        return [json.loads(i) for i in self.redis.lrange(self.uuid, 0, -1)]


class RedisSet:

    def __init__(self, host=None, port=None, db=None, param_uuid=None, data=set()):
        super().__init__(host, port, db, param_uuid)
        for item in data:
            self.add(item)

    def add(self, item):
        self.redis.sadd(self.uuid, json.dumps(item, ensure_ascii=False))

    def remove(self, item):
        self.redis.srem(self.uuid, json.dumps(item, ensure_ascii=False))

    def contains(self, item):
        return self.redis.sismember(self.uuid, json.dumps(item, ensure_ascii=False))

    def clear(self):
        self.redis.delete(self.uuid)

    def destroy(self):
        self.redis.delete(self.uuid)
        self.redis.close()

    def __len__(self):
        return self.redis.scard(self.uuid)

    def __repr__(self):
        return repr(self.redis.smembers(self.uuid))

    def __iter__(self):
        return iter(self.redis.smembers(self.uuid))


class RedisSortedSet(RedisData):

    def __init__(self, host=None, port=None, db=None, param_uuid=None, data=None):
        super().__init__(host, port, db, param_uuid)
        if data:
            for item, score in data.items():
                self.add(item, score)

    def add(self, item, score):
        self.redis.zadd(self.uuid, {json.dumps(item, ensure_ascii=False): score})
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def remove(self, item):
        self.redis.zrem(self.uuid, json.dumps(item, ensure_ascii=False))
        self.redis.expire(self.uuid, REDIS_EXPIRE_TIME)

    def get_score(self, item):
        return self.redis.zscore(self.uuid, json.dumps(item, ensure_ascii=False))

    def get_rank(self, item):
        return self.redis.zrank(self.uuid, json.dumps(item, ensure_ascii=False))

    def get_items(self, start=0, end=-1, desc=False):
        items = self.redis.zrange(self.uuid, start, end, desc=desc, withscores=True)
        return {json.loads(item.decode()): score for item, score in items}

    def __contains__(self, item):
        return self.get_score(item) is not None

    def __len__(self):
        return self.redis.zcard(self.uuid)

    def __repr__(self):
        return repr(self.get_items())


class SharedMemoryManager():

    objs = []

    @staticmethod
    def add(obj):
        SharedMemoryManager.objs.append(obj)

    @staticmethod
    def destory():
        for obj in SharedMemoryManager.objs:
            obj.destory()
    
    @staticmethod
    def serialize():
        return pickle.dumps(SharedMemoryManager.objs)

    @staticmethod
    def deserialize(data):
        SharedMemoryManager.objs = pickle.loads(data)


# class SharedMemoryDict():

#     def __init__(self, name=None, max=20000, data={}):
#         if not name:
#             name = str(uuid.uuid1())[1:6]
#         self.max_size = max
#         self.name = name
#         self.data = data
#         self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.max_size)
#         self.shm_hash = shared_memory.SharedMemory(name=name+"_hash", create=True, size=32)
#         self.lock = shared_memory.SharedMemory(name=name+"_bool", create=True, size=1)
#         self.lock.buf[:1] = b'1'
#         self.md5 = ''
#         self.using = True
#         SharedMemoryManager.add(self)
#         self.write_data(self.data)
    
#     def write_data(self, data:dict={}):
#         if not data:
#             return
#         while self.using and not int(self.lock.buf[:1]):
#             continue
#         self.data = data
#         self.lock.buf[:1] = b'0'
#         json_str = json.dumps(data).encode('utf-8')
#         s = json_str.ljust(self.max_size, b'\x00')
#         self.md5 = hashlib.md5(json_str).hexdigest()
#         self.shm.buf[:len(s)] = s
#         self.shm_hash.buf[:len(self.md5)] = self.md5.encode()
        
#         self.lock.buf[:1] = b'1'

#     def read_data(self):
#         while self.using and not int(self.lock.buf[:1]):
#             continue

#         try:
#             s_hash = self.shm_hash.buf.tobytes().decode('utf-8')
#         except Exception:
#             print("error1")
#         if s_hash == self.md5:
#             return self.data
        
#         while self.using and not int(self.lock.buf[:1]):
#             continue
        
#         try:
#             s = self.shm.buf.tobytes().rstrip(b'\x00').decode('utf-8')
#         except Exception:
#             print('error2')
#         data = json.loads(s)
#         self.data = data
#         return data

#     def destory(self):
#         self.using = False
#         while not int(self.lock.buf[:1]):
#             continue
#         self.shm.unlink()
#         self.shm_hash.unlink()
#         self.lock.unlink()

#     def __getitem__(self, key):
#         data = self.read_data()
#         if key not in data:
#             raise KeyError(key)
#         return data.get(key)

#     def __setitem__(self, key, value):
#         data = self.read_data()
#         data[key] = value
#         self.write_data(data)

#     def __delitem__(self, key):
#         data = self.read_data()
#         if key not in data:
#             raise KeyError(key)
#         del data[key]
#         self.write_data(data)
    
#     def __contains__(self, key):
#         return key in self.read_data()

#     def keys(self):
#         return self.read_data().keys()

#     def values(self):
#         return self.read_data().values()

#     def items(self):
#         return self.read_data().items()
    
#     def get(self, key, default=None):
#         data = self.read_data()
#         if key not in data:
#             return default
#         return data.get(key)

#     def update(self, data):
#         data = self.read_data()
#         for key, value in data.items():
#             self[key] = value
#         self.write_data(data)
    
#     def raw(self):
#         return self.read_data()

#     def __len__(self):
#         return len(self.read_data())

#     def __repr__(self):
#         return repr(self.read_data())
    
#     def __getstate__(self):
#         return pickle.dumps({
#             'name':self.name,
#             'max':self.max_size
#             })

#     def __setstate__(self, state):
#         data = pickle.loads(state)
#         self.name = data['name']
#         self.max_size = data['max']
#         self.shm = shared_memory.SharedMemory(name=self.name)
#         self.shm_hash = shared_memory.SharedMemory(name=self.name+"_hash")
#         self.lock = shared_memory.SharedMemory(name=self.name+"_bool")
#         self.md5 = ''
#         self.using = True
#         self.data = self.read_data()

class SharedMemoryDict():

    def __init__(self, name=None, max=20000, data={}):
        if not name:
            name = str(uuid.uuid1())[1:6]
        self.max_size = max
        self.name = name
        self.data = data
        self.shm = shared_memory.SharedMemory(name=name, create=True, size=self.max_size)
        self.shm_hash = shared_memory.SharedMemory(name=name+"_hash", create=True, size=32)
        self.md5 = ''
        self.using = True
        SharedMemoryManager.add(self)
        self.write_data(self.data)
    
    def write_data(self, data:dict={}):
        if not data:
            return
        self.data = data
        json_str = json.dumps(data).encode('utf-8')
        s = json_str.ljust(self.max_size, b'\x00')
        self.md5 = hashlib.md5(json_str).hexdigest()
        self.shm.buf[:len(s)] = s
        self.shm_hash.buf[:len(self.md5)] = self.md5.encode()

    def read_data(self):
        try:
            s_hash = self.shm_hash.buf.tobytes().decode('utf-8')
        except Exception:
            print("error1")
        if s_hash == self.md5:
            return self.data
        try:
            s = self.shm.buf.tobytes().rstrip(b'\x00').decode('utf-8')
        except Exception:
            print('error2')
        data = json.loads(s)
        self.data = data
        return data

    def destory(self):
        self.using = False
        self.shm.unlink()
        self.shm_hash.unlink()

    def __getitem__(self, key):
        data = self.read_data()
        if key not in data:
            raise KeyError(key)
        return data.get(key)

    def __setitem__(self, key, value):
        data = self.read_data()
        data[key] = value
        self.write_data(data)

    def __delitem__(self, key):
        data = self.read_data()
        if key not in data:
            raise KeyError(key)
        del data[key]
        self.write_data(data)
    
    def __contains__(self, key):
        return key in self.read_data()

    def keys(self):
        return self.read_data().keys()

    def values(self):
        return self.read_data().values()

    def items(self):
        return self.read_data().items()
    
    def get(self, key, default=None):
        data = self.read_data()
        if key not in data:
            return default
        return data.get(key)

    def update(self, data):
        data = self.read_data()
        for key, value in data.items():
            self[key] = value
        self.write_data(data)
    
    def raw(self):
        return self.read_data()

    def __len__(self):
        return len(self.read_data())

    def __repr__(self):
        return repr(self.read_data())
    
    def __getstate__(self):
        return pickle.dumps({
            'name':self.name,
            'max':self.max_size
            })

    def __setstate__(self, state):
        data = pickle.loads(state)
        self.name = data['name']
        self.max_size = data['max']
        self.shm = shared_memory.SharedMemory(name=self.name)
        self.shm_hash = shared_memory.SharedMemory(name=self.name+"_hash")
        self.md5 = ''
        self.using = True
        self.data = self.read_data()
