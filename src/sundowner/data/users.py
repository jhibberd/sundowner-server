import tornado.gen
from bson.objectid import ObjectId


class Data(object):

    def __init__(self, db):
        """See sundowner.data"""
        self._coll = db.users

    @tornado.gen.coroutine
    def ensure_indexes(self):
        yield self._coll.ensure_index("facebook.id", unique=True)

    @tornado.gen.coroutine
    def get_by_facebook_id(self, facebook_id):
        doc = yield self._coll.find_one({"facebook.id": facebook_id})
        raise tornado.gen.Return(doc)

    @tornado.gen.coroutine
    def create_from_facebook_data(self, data):
        user_id = ObjectId()
        assert "id" in data
        assert "name" in data
        yield self._coll.insert({
            "_id":          user_id,
            "facebook":     data,
            })
        raise tornado.gen.Return({
            "id":       user_id,
            "name":     data["name"],
            })

    @tornado.gen.coroutine
    def get_usernames(self, user_ids):
        """Resolve a list of user IDs to usernames."""
        cursor = self._coll.find(
            {'_id': {'$in': user_ids}}, {'facebook.name': 1})
        result = yield cursor.to_list(length=10)
        result = dict([(d['_id'], d['facebook']["name"]) for d in result])
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def exists(self, user_id):
        """Return whether a user ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield self._coll.find(
            {'_id': ObjectId(user_id)}, {'_id': 1}).limit(1).count()
        raise tornado.gen.Return(count == 1)

