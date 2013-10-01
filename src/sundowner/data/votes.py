import pymongo
import pymongo.errors
import tornado.gen
from bson.objectid import ObjectId

class Vote(object):
    DOWN =  0
    UP =    1

class Data(object):

    def __init__(self, db):
        """See sundowner.data"""
        self._coll = db.votes

    @tornado.gen.coroutine
    def ensure_indexes(self):
        yield self._coll.ensure_index([
            ('user_id',     pymongo.ASCENDING),
            ('content_id',  pymongo.ASCENDING),
            ('vote',        pymongo.ASCENDING),
            ], unique=True)

    @tornado.gen.coroutine
    def put(self, user_id, content_id, vote):
        """Register a user voting content up or down.

        Returns whether the vote was successfully registered.
        """
        try:
            yield self._coll.insert({
                'user_id':      ObjectId(user_id),
                'content_id':   ObjectId(content_id),
                'vote':         vote,
                })
        except pymongo.errors.DuplicateKeyError:
            # that vote has already been made
            raise tornado.gen.Return(False)
        else:
            raise tornado.gen.Return(True)

