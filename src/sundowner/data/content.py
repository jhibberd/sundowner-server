"""Abstraction of the mongoDB collection used to store, retrieve and update
content.
"""

import pymongo
import time
import tornado.gen
from bson.objectid import ObjectId
from sundowner.data.votes import Vote


class Data(object):

    QUERY_RADIUS =  2000    # meters (used by ranking module)
    EARTH_RADIUS =  6371000 # meters (used by ranking module)

    def __init__(self, db):
        """See sundowner.data"""
        self._coll = db.content
    
    @tornado.gen.coroutine
    def ensure_indexes(self):
       yield self._coll.ensure_index([('loc', pymongo.GEOSPHERE)])

    @tornado.gen.coroutine
    def get_nearby(self, lng, lat):
        """Return an unsorted list of all content occurring within a circle on
        the Earth's surface with point (lng, lat) and radius 'QUERY_RADIUS'.
        """

        # http://docs.mongodb.org/manual/reference/operator/centerSphere/#op._S_centerSphere
        # http://docs.mongodb.org/manual/tutorial/calculate-distances-using-spherical-geometry-with-2d-geospatial-indexes/
        QUERY_RADIUS_RADIANS = float(Data.QUERY_RADIUS) / Data.EARTH_RADIUS
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
        cursor = self._coll.find(spec)
        result = yield cursor.to_list(length=10000)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def put(self, content):
        """Save new content to the database."""
        content['user_id'] = ObjectId(content['user_id'])
        content['created'] = long(time.time())
        yield self._coll.insert(content)

    @tornado.gen.coroutine
    def inc_vote(self, content_id, vote):
        """Increment either the votes up or down count for the content."""
        assert vote in [Vote.UP, Vote.DOWN]
        field = 'votes.up' if vote == Vote.UP else 'votes.down'
        yield self._coll.update(
            {'_id': ObjectId(content_id)}, {'$inc': {field: 1}}) 

    @tornado.gen.coroutine
    def exists(self, content_id):
        """Return whether a content ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield self._coll.find(
            {'_id': ObjectId(content_id)}, {'_id': 1}).limit(1).count()
        raise tornado.gen.Return(count == 1)

