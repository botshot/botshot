from .key_value_store import KeyValueStore
from .redis_store import RedisStore


DATABASE = RedisStore()  # TODO


def get_string(key: str, lang: str):
    key = lang + "_" + key
    return DATABASE.get(key)
