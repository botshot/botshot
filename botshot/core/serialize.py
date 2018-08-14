import dateutil.parser

from botshot.core.entity_value import EntityValue


def json_deserialize(obj):
    #print('Deserializing:', obj)
    if obj.get('__type__') == 'datetime':
        return dateutil.parser.parse(obj.get('value'))
    elif obj.get('__type__') == 'entity':
        return EntityValue(**obj.get('data'))
    return obj


def json_serialize(obj):
    from datetime import datetime
    if isinstance(obj, datetime):
        return {'__type__':'datetime', 'value': obj.isoformat()}
    elif isinstance(obj, EntityValue):
        return {'__type__': 'entity', 'data': obj.__dict__}
    else:
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
