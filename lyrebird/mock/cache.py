from collections import deque
from lyrebird.utils import RedisList, RedisDict
from lyrebird import application
from lyrebird.log import get_logger

_cache = None
logger = None


def get_cache():
    global _cache
    global logger
    if not _cache and application.config.get('redis_enable', False):
        _cache = RedisCache()
    elif not _cache:
        # todo 此处应根据配置，决定生成ListCache还是RedisCache
        _cache = ListCache()
    if not logger:
        logger = get_logger()
    return _cache


class ListCache:
    """
    双向序列
    默认最大值1000
    存储流经mock服务的数据
    
    """
    def __init__(self, maxlen=1000):
        self._cache = deque(maxlen=maxlen)

    def add(self, obj):
        self._cache.append(obj)

    def items(self):
        return list(self._cache)

    def get(self, id_):
        for item in list(self._cache):
            if item['id'] != id_:
                continue
            return item

    def clear(self):
        self._cache.clear()
    
    def delete(self, obj):
        self._cache.remove(obj)
    
    def delete_by_ids(self, *ids):
        del_items = []
        for item in list(self._cache):
            if item['id'] in ids:
                del_items.append(item)
        for item in del_items:
            self.delete(item)

class RedisCache(RedisDict):
    """
    如果部署在服务器上，并使用多进程，需要使用redis存储数据，实现多进程共享数据
    RedisCache在使用上可以被视为一个list,另外封装部分get、item等部分dict接口
    RedisCache由一个RedisDict和一个RedisList组成:
        字典结构用于存储数据并快速查找对应id的数据,key为flow的id,value为整个flow
        list结构用于维护队列数据的先后顺序,其中仅存储flow的id
    """
    def __init__(self, maxlen=1000):
        super().__init__()
        self.indexs = RedisList()
        self.MAX_LENGTH = maxlen

    def append(self, data):
        if not RedisCache.check_id(data):
            return
        # try:
        id = data['id']
        super().__setitem__(id, data)
        self.indexs.append(id)
        # except Exception as e:
        #     print(f'11111111  {id} : {e}')
        if self.indexs.redis.llen(self.uuid) > self.MAX_LENGTH:
            removed_id = self.indexs.redis.lindex('mylist', 0)
            self.indexs.redis.ltrim(self.uuid, 1, -1)
            super().__delitem__(removed_id)

    def add(self, obj):
        try:
            self.append(obj)
        except Exception as e:
            pass

    def get(self, id, default=None):
        return super().get(id, default)

    def items(self):
        return self.raw()

    def delete(self, obj):
        if not RedisCache.check_id(obj):
            return
        id = obj['id']
        idx = self.indexs.index(id)
        del self[id]
        del self.indexs[idx]
    
    def delete_by_id(self, id):
        if not id:
            return
        idx = self.indexs.index(id)
        del self[id]
        del self.indexs[idx]

    def delete_by_ids(self, *ids):
        if not ids:
            return
        for id in ids:
            self.delete_by_id(id)
    
    def clear(self):
        super().clear()
        self.indexs.clear()
    
    def raw(self):
        map = super().raw()
        idxs = self.indexs.raw()
        return [map[i] for i in idxs if i in map]
    
    def __getitem__(self, index):
        return self.get(self.indexs[index])

    def __setitem__(self, index, value):
        if not RedisCache.check_id(value):
            return
        self.indexs[index] = value['id']
        super().__setitem__(value['id'], value)

    def __delitem__(self, index):
        id = self.indexs[index]
        del self.indexs[index]
        super().__delitem__(id)

    def __contains__(self, value):
        id = value.get('id')
        return True if id and id in self else False

    def __len__(self):
        return super.__len__()

    def __repr__(self):
        return f'RedisCache(host={self.host},port={self.port},db={self.db},size={len(self)})'

    def extend(self, values):
        for v in values:
            self.append(v)

    def pop(self, index=-1):
        id = self.indexs.pop(index)
        value = super().__getitem__(id)
        super().__delitem__(id)
        return value

    def index(self, value, start=None, end=None):
        if not RedisCache.check_id(value):
            return
        id = value['id']
        return self.indexs.index(id, start, end)

    @staticmethod
    def check_id(data):
        if 'id' not in data:
            logger.error(f'Key Error in RedisCache, the key field \"id\" is missing from the data:{data}')
            return False
        return True


class FileCache:
    pass
