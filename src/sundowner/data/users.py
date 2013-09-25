import tornado.gen
from bson.objectid import ObjectId


class Data(object):

    @classmethod
    @tornado.gen.coroutine
    def init(cls, db):
        """See sundowner.data"""
        cls._coll = db.users
        yield cls._coll.ensure_index('username', unique=True)

    @classmethod
    @tornado.gen.coroutine
    def get_id(cls, username, create_if_not_found=False):
        """Return the ObjectId associated with the username or None if the
        username doesn't exist.

        If 'create_if_not_found' is true then an ID will be created in the
        database if the username doesn't exist.
        """
        doc = yield cls._coll.find_one({'username': username})
        if doc:
            raise tornado.gen.Return(doc['_id'])
        elif create_if_not_found:
            doc_id = ObjectId()
            yield cls._coll.insert({'_id': doc_id, 'username': username})
            raise tornado.gen.Return(doc_id)
        else:
            raise tornado.gen.Return(None)

    @classmethod
    @tornado.gen.coroutine
    def get_usernames(cls, user_ids):
        """Resolve a list of user IDs to usernames."""
        cursor = cls._coll.find(
            {'_id': {'$in': user_ids}}, {'username': 1})
        result = []
        while (yield cursor.fetch_next):
            doc = cursor.next_object()
            result.append((doc['_id'], doc['username']))
        raise tornado.gen.Return(dict(result))

    @classmethod
    @tornado.gen.coroutine
    def exists(cls, user_id):
        """Return whether a user ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield cls._coll.find(
            {'_id': ObjectId(user_id)}, {'_id': 1}).limit(1).count()
        raise tornado.gen.Return(count == 1)

