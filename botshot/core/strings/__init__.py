from .key_value_store import KeyValueStore
from .redis_store import RedisStore
from .web import *

DATABASE = RedisStore()  # TODO


def get_string(key: str, lang: str):
    key = lang + "_" + key
    return DATABASE.get(key, lang)


def update_view(req):
    print(req.POST)
    return HttpResponse(200)
