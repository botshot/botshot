import logging
import warnings

import redis
import pickle
import dateutil.parser
from urllib.parse import urlparse
from base64 import b64encode, b64decode

from django.conf import settings
from django.utils.module_loading import import_string

from botshot.core import config
from botshot.core.entity_value import EntityValue

_connection_pool = None
_redis = None


class DictSerializable:
    """
    Marker class used only to specify that our class can be serialized using its __dict__ field
    Inheriting from this class is enforced instead of trying to serialize any object to avoid unexpected errors
    when serializing objects that should not be serialized.

    Callables and fields starting with _ are ignored.
    The deserialized fields are passed in the constructor as kwargs.
    """
    pass


def get_redis():
    """
    Returns an instance of Redis cache, or None if Redis is not configured. 
    """
    global _connection_pool
    global _redis
    if not _connection_pool:
        redis_url = config.get('REDIS_URL')
        if not redis_url:
            warnings.warn("Redis not available, returning None. Set REDIS_URL in BOT_CONFIG to enable cache.")
            return None
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
    """
    Attempts to recursively deserialize an object from its JSON representation.
    Any items containing the __type__ key will be loaded as instances of the corresponding class.
    If this is not possible, the function will return None and an error will be logged.

    Attributes starting with '__' will be ignored.

    :param obj: The object to be deserialized. Should be loaded using json.loads().
    :return: The deserialized object.
    """
    try:
        if isinstance(obj, list):
            return [json_deserialize(item) for item in obj]
        elif not isinstance(obj, dict):
            return obj
        obj_type = obj.get('__type__')
        if obj_type == 'datetime':
            return dateutil.parser.parse(obj.get('value'))
        elif obj_type == 'entity':
            bytearr = str.encode(obj.get("__data__"))
            return pickle.loads(b64decode(bytearr))
        data = {}
        for k, v in obj.items():
            if not k.startswith("__"):
                data[k] = json_deserialize(v)
        if obj_type:
            return import_string(obj_type)(**data)
        return data
    except Exception:
        logging.exception("Error deserializing object: %s" % obj)
        return None


def json_serialize(obj):
    """
    Attempts to recursively serialize an object to a JSON representation.
    Any objects extending the DictSerializable class will be serialized using their __dict__ property.

    Attributes starting with '__' will be ignored.

    :param obj: The object to be serialized.
    :return: The JSON representation. Should be saved with json.dumps().
    """
    try:
        from datetime import datetime
        # from botshot.core.entities import Entity
        if isinstance(obj, dict):
            data = {}
            for k, v in obj.items():
                data[k] = json_serialize(v)
            return data
        elif hasattr(obj, '__iter__') and not isinstance(obj, str):
            return [json_serialize(item) for item in obj]
        if isinstance(obj, datetime):
            return {'__type__': 'datetime', 'value': obj.isoformat()}
        elif isinstance(obj, EntityValue):
            data = b64encode(pickle.dumps(obj))
            return {"__data__": data.decode('utf8'), '__type__': 'entity'}
        elif isinstance(obj, DictSerializable):
            data = {}
            for k, v in obj.__dict__.items():
                if not callable(v) and not k.startswith('__'):
                    data[k] = json_serialize(v)
            data['__type__'] = fullname(obj)
            return data
        return obj
    except Exception:
        logging.exception("Error serializing object: %s" % obj)
        return None
