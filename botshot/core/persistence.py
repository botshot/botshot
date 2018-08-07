import redis
from django.conf import settings
from urllib.parse import urlparse

_connection_pool = None
_redis = None


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
