import tornado.gen
from bson.objectid import ObjectId


class Data(object):

    def __init__(self, db):
        """See sundowner.data"""
        self._coll = db.users

    @tornado.gen.coroutine
    def ensure_indexes(self):
        yield self._coll.ensure_index('username', unique=True)

    @tornado.gen.coroutine
    def get_id(self, username, create_if_not_found=False):
        """Return the ObjectId associated with the username or None if the
        username doesn't exist.

        If 'create_if_not_found' is true then an ID will be created in the
        database if the username doesn't exist.
        """
        doc = yield self._coll.find_one({'username': username})
        if doc:
            raise tornado.gen.Return(doc['_id'])
        elif create_if_not_found:
            doc_id = ObjectId()
            yield self._coll.insert({'_id': doc_id, 'username': username})
            raise tornado.gen.Return(doc_id)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def get_usernames(self, user_ids):
        """Resolve a list of user IDs to usernames."""
        cursor = self._coll.find(
            {'_id': {'$in': user_ids}}, {'username': 1})
        result = cursor.to_list(length=10)
        result = dict([(d['_id'], d['username']) for d in result])
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def exists(self, user_id):
        """Return whether a user ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield self._coll.find(
            {'_id': ObjectId(user_id)}, {'_id': 1}).limit(1).count()
        raise tornado.gen.Return(count == 1)

