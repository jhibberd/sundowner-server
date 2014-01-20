import redis
import sundowner.config


class _ThreadSafeCacheConnection(object):

    @classmethod
    def get(cls):
        if not hasattr(cls, "_conn"):
            cls._conn = redis.Redis(
                host=   sundowner.config.cfg["cache-host"],
                port=   sundowner.config.cfg["cache-port"],
                db=     sundowner.config.cfg["cache-db"],
                )
        return cls._conn


class CacheBase(object):
    """Superclass for cache classes that provides access to a single 
    thread-safe connection to the caching service.
    """

    @staticmethod
    def get_conn():
        return _ThreadSafeCacheConnection.get()

