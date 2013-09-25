"""Abstraction of the mongoDB collection used to store, retrieve and update
content.
"""

import pymongo
import time
import tornado.gen
from bson.objectid import ObjectId
from sundowner.data.votes import Vote


QUERY_RADIUS =  2000    # meters (used by ranking module)
EARTH_RADIUS =  6371000 # meters (used by ranking module)

class Data(object):

    @classmethod
    @tornado.gen.coroutine
    def init(cls, db):
        """See sundowner.data"""
        cls._coll = db.content
        yield cls._coll.ensure_index([('loc', pymongo.GEOSPHERE)])
    
    @classmethod
    @tornado.gen.coroutine
    def get_nearby(cls, lng, lat):
        """Return an unsorted list of all content occurring within a circle on
        the Earth's surface with point (lng, lat) and radius 'QUERY_RADIUS'.
        """

        # http://docs.mongodb.org/manual/reference/operator/centerSphere/#op._S_centerSphere
        # http://docs.mongodb.org/manual/tutorial/calculate-distances-using-spherical-geometry-with-2d-geospatial-indexes/
        QUERY_RADIUS_RADIANS = float(QUERY_RADIUS) / EARTH_RADIUS
        spec = {
            'loc': {
                '$geoWithin': {
                    '$centerSphere': [[lng, lat], QUERY_RADIUS_RADIANS],
                    },
                },
            }

        # NOTE The number of content docs being returned isn't being limited 
        # which might be a problem in areas with lots of content. A better, but 
        # more complex, solution might be to calculate the query radius based 
        # on the concentration of content in an area.
        result = []
        cursor = cls._coll.find(spec)
        while (yield cursor.fetch_next):
            result.append(cursor.next_object())
        raise tornado.gen.Return(result)

    @classmethod
    @tornado.gen.coroutine
    def put(cls, content):
        """Save new content to the database."""
        content['user_id'] = ObjectId(content['user_id'])
        content['created'] = long(time.time())
        yield cls._coll.insert(content)

    @classmethod
    @tornado.gen.coroutine
    def inc_vote(cls, content_id, vote):
        """Increment either the votes up or down count for the content."""
        assert vote in [Vote.UP, Vote.DOWN]
        field = 'votes.up' if vote == Vote.UP else 'votes.down'
        yield cls._coll.update(
            {'_id': ObjectId(content_id)}, {'$inc': {field: 1}}) 

    @classmethod
    @tornado.gen.coroutine
    def exists(cls, content_id):
        """Return whether a content ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield cls._coll.find(
            {'_id': ObjectId(content_id)}, {'_id': 1}).limit(1).count()
        raise tornado.gen.Return(count == 1)

