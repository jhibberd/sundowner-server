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
    def get_user_votes(self, user_id):
        """Return a set of content that the user has votes on in the form:

            [(content, vote), ...]

            eg.

            [(ARTICLE_FOO, VOTE_UP), ...]

        The compound index on this collection is designed to cover this query,
        which can be seen by calling 'explain' on the cursor and observing
        that the 'indexOnly' propery is true.
        http://docs.mongodb.org/manual/tutorial/create-indexes-to-support-queries/#indexes-covered-queries

        A set is returned in favour of a list because order is irrelevant and 
        inclusion tests have to be fast in order to filter content in realtime.

        NOTE if the number of votes issued by a single user becomes too large
        to fit into memory it might be worth adding a geospatial index to this
        collection too
        """

        result = []
        cursor = self._coll.find(
            spec={'user_id': ObjectId(user_id)},
            fields={
                '_id':          0,
                'content_id':   1,
                'vote':         1,
                })
        while (yield cursor.fetch_next):
            doc = cursor.next_object()
            result.append((doc['content_id'], doc['vote']))
        raise tornado.gen.Return(result)

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

