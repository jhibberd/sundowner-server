import sundowner.cache
from bson.objectid import ObjectId


class FriendsCache(sundowner.cache.CacheBase):
    """Cache the set of friends for users.

    Each friend is expressed as a native ID (not Facebook ID) of type ObjectId.

    Friends are stored as a comma-separated string. This is because the list
    is always get/set in its entirety. We wouldn't benefit from using Redis'
    commands for manipulating sets in memory. Also, replacing the set (if it
    was stored as a Redis set) couldn't be done atomically; we would first
    need to delete the set, then re-set it.
    """

    @classmethod
    def get(cls, user_id):
        """Get the set of friends for a user."""
        k = cls._key(user_id)
        friends = cls.get_conn().get(k)
        if friends is None:
            return None
        friends = friends.split(',')
        friends = map(ObjectId, friends)
        friends = set(friends)
        return friends

    @classmethod
    def put(cls, user_id, friends):
        """Put the set of friends for a user."""
        friends = map(str, friends) # from ObjectId
        friends = ','.join(friends)
        k = cls._key(user_id)
        cls.get_conn().set(k, friends)

    @classmethod
    def clear(cls, user_id):
        """Clear the set of friends for a user.

        Typically because new friend data has been retrieved from Facebook.
        """
        k = cls._key(user_id)
        cls.get_conn().delete(k)

    @staticmethod
    def _key(user_id):
        return "friends/%s" % user_id

