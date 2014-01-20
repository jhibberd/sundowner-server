import motor
import pymongo
import tornado.gen
from bson.objectid import ObjectId
from operator import itemgetter


class Data(object):

    def __init__(self, db):
        """See sundowner.data"""
        self._conn = db.users

    @tornado.gen.coroutine
    def ensure_indexes(self):
        # in order for `read_native_user_ids_from_facebook_user_ids` to be
        # covered the field being queried cannot use dot notation
        return self._conn.ensure_index([
            ("facebook_id", pymongo.ASCENDING), ("_id", pymongo.ASCENDING)], 
            unique=True)

    @tornado.gen.coroutine
    def create(self, user_record):
        
        # assert that the user record has the required fields
        assert "id" in user_record["facebook"]
        assert "name" in user_record["facebook"]
        
        user_id = ObjectId()
        user_record["_id"] = user_id
        yield motor.Op(self._conn.insert, user_record)
        raise tornado.gen.Return(user_id)

    @tornado.gen.coroutine
    def read(self, user_id):
        doc = yield motor.Op(self._conn.find_one, {"_id": user_id})
        raise tornado.gen.Return(doc)

    # The first page of friends returned by the Facebook Graph API for a user
    # is limited to 5000
    _MAX_FRIENDS = 5000
    @tornado.gen.coroutine
    def read_native_user_ids_from_facebook_user_ids(self, fb_user_ids):
        """Return the native user IDs of users whose Facebook ID is in the list
        `fb_user_ids`.

        The native user IDs are of type ObjectId.
        """

        # this query is covered by the `facebook_id` index
        cursor = self._conn.find(
            {"facebook_id": {"$in": fb_user_ids}}, {"_id": 1})
        # impose a cursor limit to suppress warning
        cursor.limit(self._MAX_FRIENDS)

        # uncomment to check it is covered by the index
        #result = yield motor.Op(cursor.explain); raise Exception(result)

        result = yield motor.Op(cursor.to_list)
        result = map(itemgetter("_id"), result)
        result = set(result)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def read_by_facebook_user_id(self, fb_user_id):
        doc = yield motor.Op(self._conn.find_one, {"facebook.id": fb_user_id})
        raise tornado.gen.Return(doc)

    @tornado.gen.coroutine
    def get_usernames(self, user_ids):
        """Resolve a list of user IDs to usernames."""
        if not user_ids:
            raise tornado.gen.Return({})
        user_ids = list(user_ids) # MongoDB spec doesn't accept sets
        cursor = self._conn.find(
            {"_id": {"$in": user_ids}}, {"facebook.name": 1})
        result = yield motor.Op(cursor.to_list, length=10)
        result = dict([(d["_id"], d["facebook"]["name"]) for d in result])
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def update(self, doc):
        yield motor.Op(self._conn.update, {"_id": doc["_id"]}, doc)

