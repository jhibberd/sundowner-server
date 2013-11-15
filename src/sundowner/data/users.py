import tornado.gen
from bson.objectid import ObjectId


class Data(object):

    def __init__(self, db):
        """See sundowner.data"""
        self._conn = db.users

    @tornado.gen.coroutine
    def ensure_indexes(self):
        return self._conn.ensure_index("facebook.id", unique=True)

    @tornado.gen.coroutine
    def create(self, user_meta):
        user_id = ObjectId()
        assert "id" in user_meta
        assert "name" in user_meta
        yield self._conn.insert({
            "_id":          user_id,
            "facebook":     user_meta,
            })
        raise tornado.gen.Return(user_id)

    @tornado.gen.coroutine
    def read_by_facebook_user_id(self, fb_user_id):
        doc = yield self._conn.find_one({"facebook.id": fb_user_id})
        raise tornado.gen.Return(doc)

    @tornado.gen.coroutine
    def get_usernames(self, user_ids):
        """Resolve a list of user IDs to usernames."""
        cursor = self._conn.find(
            {'_id': {'$in': user_ids}}, {'facebook.name': 1})
        result = yield cursor.to_list(length=10)
        result = dict([(d['_id'], d['facebook']["name"]) for d in result])
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def update(self, doc):
        yield self._conn.update({"_id": doc["_id"]}, doc)

