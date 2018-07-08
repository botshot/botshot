from botshot.core import persistence
from .key_value_store import KeyValueStore


class RedisStore(KeyValueStore):

    def __init__(self, prefix="string__"):

        if not isinstance(prefix, str) or not len(prefix):
            raise ValueError("Redis prefix must be a non-empty string")

        self.redis = persistence.get_redis()
        self.prefix = prefix

    def update(self, key: str, value: str):
        self.validate_key(key)
        self.validate_value(value)
        return self.redis.set(name=self.prefix + key, value=value.encode('utf8'))

    def delete(self, key: str):
        self.validate_key(key)
        return self.redis.delete(self.prefix + key)

    def get(self, key: str):
        self.validate_key(key)
        val = self.redis.get(self.prefix + key)
        return val.decode('utf8') if val else None

    def __contains__(self, key: str):
        self.validate_value(key)
        return self.redis.exists(self.prefix + key)
