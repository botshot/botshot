from base64 import b64encode, b64decode

import dateutil.parser
import pickle

from botshot.core.entity_value import EntityValue


# FIXME just pickle the whole thing instead of serializing

def json_deserialize(obj):
    #print('Deserializing:', obj)
    if obj.get('__type__') == 'datetime':
        return dateutil.parser.parse(obj.get('value'))
    elif obj.get('__type__') == 'entity':
        bytearr = str.encode(obj.get("__data__"))
        return pickle.loads(b64decode(bytearr))
    return obj


def json_serialize(obj):
    from datetime import datetime
    # from botshot.core.entities import Entity
    if isinstance(obj, datetime):
        return {'__type__':'datetime', 'value': obj.isoformat()}
    elif isinstance(obj, EntityValue):
        data = b64encode(pickle.dumps(obj))
        return {"__data__": data.decode('utf8'), '__type__': 'entity'}
    raise TypeError ("Error saving entity value. Type %s not serializable: %s" % (type(obj), obj))
