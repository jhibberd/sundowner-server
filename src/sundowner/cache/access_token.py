import sundowner.cache
import time
from bson.objectid import ObjectId


class AccessTokenCache(sundowner.cache.CacheBase):
    """Cache user IDs by access token."""

    @classmethod
    def get(cls, access_token):
        key = cls._key(access_token)
        user_id = cls.get_conn().get(key)
        if user_id is None:
            return None
        else:
            return ObjectId(user_id)

    @classmethod
    def put(cls, access_token, user_id, expiry):
        key = cls._key(access_token)
        cls.get_conn().set(
            name=   key, 
            value=  str(user_id),                   # from ObjectId
            ex=     (expiry - long(time.time()))    # from timestamp to secs
            )

    @staticmethod
    def _key(access_token):
        return "auth/%s" % access_token

