from bson.objectid import ObjectId


class Data(object):

    @classmethod
    def init(cls, conn):
        """See sundowner.data"""
        cls._collection = conn.users
        cls._collection.ensure_index('username', unique=True)

    @classmethod
    def get_id(cls, username, create_if_not_found=False):
        """Return the ObjectId associated with the username or None if the
        username doesn't exist.

        If 'create_if_not_found' is true then an ID will be created in the
        database if the username doesn't exist.
        """
        doc = cls._collection.find_one({'username': username})
        if doc:
            return doc['_id']
        elif create_if_not_found:
            doc_id = ObjectId()
            cls._collection.insert({'_id': doc_id, 'username': username})
            return doc_id
        else:
            return None

    @classmethod
    def get_usernames(cls, user_ids):
        """Resolve a list of user IDs to usernames."""
        cursor = cls._collection.find(
            {'_id': {'$in': user_ids}}, {'username': 1})
        return dict([(doc['_id'], doc['username']) for doc in cursor])

    @classmethod
    def exists(cls, user_id):
        """Return whether a user ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        return cls._collection.find(
            {'_id': ObjectId(user_id)}, {'_id': 1}).limit(1).count() == 1

