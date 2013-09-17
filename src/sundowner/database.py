"""Abstraction of the mongoDB collection used to store, retrieve and update
content.
"""

import pymongo


QUERY_RADIUS =  2000    # meters (used by ranking module)
EARTH_RADIUS =  6371000 # meters (used by ranking module)

class Database(object):

    @classmethod
    def connect(cls, host='localhost', port=27017):
        """Create a global connection to mongoDB.

        The connection is thread-safe:
        http://api.mongodb.org/python/current/faq.html#is-pymongo-thread-safe
        """
        cls._content_collection = \
            pymongo.MongoClient(host, port).sundowner_instagram.content
    
    @classmethod
    def get_content_nearby(cls, lng, lat):
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
        return list(cls._content_collection.find(spec))

    @classmethod
    def put(cls, content):
        """Save new content to the database."""
        cls._content_collection.insert(content)

