"""Abstraction of the mongoDB collection used to store, retrieve and update
content.
"""

from bson.objectid import ObjectId


QUERY_RADIUS =  2000    # meters (used by ranking module)
EARTH_RADIUS =  6371000 # meters (used by ranking module)

class Data(object):

    @classmethod
    def init(cls, conn):
        """See sundowner.data"""
        cls._collection = conn.content
    
    @classmethod
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
        return list(cls._collection.find(spec))

    @classmethod
    def put(cls, content):
        """Save new content to the database."""
        cls._collection.insert(content)

    @classmethod
    def inc_vote(cls, content_id, vote):
        """Increment either the votes up or down count for the content."""
        assert vote in [Vote.UP, Vote.DOWN]
        field = 'votes.up' if vote == Vote.UP else 'votes.down'
        cls._collection.update(
            {"_id", ObjectId(content_id)}, {'$inc': {field: 1}}) 

