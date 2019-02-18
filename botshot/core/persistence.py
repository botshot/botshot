import redis
import pickle
import dateutil.parser
from urllib.parse import urlparse
from base64 import b64encode, b64decode

from django.conf import settings
from django.utils.module_loading import import_string

from botshot.core.entity_value import EntityValue

_connection_pool = None
_redis = None


class DictSerializable:
    """
    Marker class used only to specify that our class can be serialized using its __dict__ field
    Inheriting from this class is enforced instead of trying to serialize any object to avoid unexpected errors when serializing objects that should not be serialized
    """
    pass


def get_redis():
    global _connection_pool
    global _redis
    if not _connection_pool:
        redis_url = settings.BOT_CONFIG.get('REDIS_URL')
        if not redis_url:
            raise Exception('REDIS_URL cannot be blank')
        redis_url_parsed = urlparse(redis_url)

        _connection_pool = redis.ConnectionPool(
            host=redis_url_parsed.hostname,
            port=redis_url_parsed.port,
            password=redis_url_parsed.password,
            db=0,
            max_connections=2
        )
    if not _redis:
        _redis = redis.StrictRedis(connection_pool=_connection_pool)
    return _redis


def fullname(o):
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__  # Avoid reporting __builtin__
    return module + '.' + o.__class__.__name__


def json_deserialize(obj):
    #print('Deserializing:', obj)
    obj_type = obj.get('__type__')
    if obj_type == 'datetime':
        return dateutil.parser.parse(obj.get('value'))
    elif obj_type == 'entity':
        bytearr = str.encode(obj.get("__data__"))
        return pickle.loads(b64decode(bytearr))
    elif obj_type:
        return import_string(obj_type)(**obj.get("__dict__"))
    return obj


def json_serialize(obj):
    from datetime import datetime
    # from botshot.core.entities import Entity
    if isinstance(obj, datetime):
        return {'__type__':'datetime', 'value': obj.isoformat()}
    elif isinstance(obj, EntityValue):
        data = b64encode(pickle.dumps(obj))
        return {"__data__": data.decode('utf8'), '__type__': 'entity'}
    elif isinstance(obj, DictSerializable):
        return {'__dict__': obj.__dict__, '__type__': fullname(obj)}
    return obj


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey))
            for key, value in obj.__dict__.items()
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj
