import pymongo
import pymongo.errors
from bson.objectid import ObjectId


class Data(object):

    @classmethod
    def init(cls, conn):
        """See sundowner.data"""
        cls._collection = conn.votes
        cls._collection.ensure_index([
            ('user_id',     pymongo.ASCENDING),
            ('content_id',  pymongo.ASCENDING),
            ('vote',        pymongo.ASCENDING),
            ], unique=True)

    @classmethod
    def get_user_votes(cls, user_id):
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

        cursor = cls._collection.find(
            spec={'user_id': ObjectId(user_id)},
            fields={
                '_id':          0,
                'content_id':   1,
                'vote':         1,
                })

        shorten = lambda doc: (doc['content_id'], doc['vote'])
        return set(map(shorten, cursor))

    @classmethod
    def put(cls, user_id, content_id, vote):
        """Register a user voting content up or down.

        Returns whether the vote was successfully registered.
        """
        try:
            cls._collection.insert({
                'user_id':      ObjectId(user_id),
                'content_id':   ObjectId(content_id),
                'vote':         vote,
                })
        except pymongo.errors.DuplicateKeyError:
            # that vote has already been made
            return False
        else:
            return True


class Vote(object):
    DOWN =  0
    UP =    1

