from botshot.core import persistence
from .key_value_store import KeyValueStore


class RedisStore(KeyValueStore):

    def __init__(self, prefix="string__"):

        if not isinstance(prefix, str) or not len(prefix):
            raise ValueError("Redis prefix must be a non-empty string")

        self.redis = persistence.get_redis()
        self.prefix = prefix

    def get_prefix(self, lang):
        lang = str(lang) + "__" if lang else ""
        return self.prefix + lang

    def update(self, key: str, value: str, lang):
        self.validate_key(key)
        self.validate_value(value)
        return self.redis.set(name=self.get_prefix(lang) + lang + key, value=value.encode('utf8'))

    def delete(self, key: str, lang):
        self.validate_key(key)
        return self.redis.delete(self.get_prefix(lang) + key)

    def get(self, key: str, lang):
        self.validate_key(key)
        val = self.redis.get(self.get_prefix(lang) + key)
        return val.decode('utf8') if val else None

    def __contains__(self, key: str, lang):
        self.validate_value(key)
        return self.redis.exists(self.get_prefix(lang) + key)
