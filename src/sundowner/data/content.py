"""Abstraction of the mongoDB collection used to store, retrieve and update
content.
"""

import motor
import pymongo
import sundowner.config
import time
import tornado.gen
from bson.objectid import ObjectId
from sundowner.data.votes import Vote


class Data(object):

    QUERY_RADIUS =  1000    # meters (used in model)
    EARTH_RADIUS =  6371000 # meters (used in model)

    def __init__(self, db):
        """See sundowner.data"""
        self._conn = db.content
    
    @tornado.gen.coroutine
    def ensure_indexes(self):
        # instead of explicity sorting the results by the 'score' field we're
        # relying on the fact that the compound index will already be storing
        # the documents in this order
        yield motor.Op(self._conn.ensure_index, [
            ("loc",             pymongo.GEOSPHERE), 
            ("score.overall",   pymongo.DESCENDING),
            ])

    # http://docs.mongodb.org/manual/reference/operator/centerSphere/#op._S_centerSphere
    # http://docs.mongodb.org/manual/tutorial/calculate-distances-using-spherical-geometry-with-2d-geospatial-indexes/
    _QUERY_RADIUS_RADIANS = float(QUERY_RADIUS) / EARTH_RADIUS

    @tornado.gen.coroutine
    def get_nearby(self, lng, lat, friends, limit_friends, limit_final):
        """Return an unsorted list of up to `limit_final` tags occurring within
        a circle on the Earth's surface with point (lng, lat) and radius 
        'QUERY_RADIUS'.
        """

        # the pipeline doesn't appear to support an $in operator, so the next
        # best way to test for list inclusion if a list of OR conditions
        is_friend_cond = {
            "$or": map(lambda f: {"$eq": ["$user_id", f]}, friends),
            }

        weights = sundowner.config.cfg["score-weights"]

        spec = [{

            # get top scoring (because of compound index) tags within a radius 
            # of a lng/lat
            # NOTE: the geoNear aggregation pipeline operator was tried here
            # but it was slower
            "$match": {
                "loc": {
                    "$geoWithin": {
                        "$centerSphere": [
                                    [lng, lat], self._QUERY_RADIUS_RADIANS],
                        },
                    },
                }
            }, {

            # Limit batch size before assessing whether each tag was made by
            # a friend of the user. This ensures that the algorithm is 
            # performant even if a large number of tags are created in a small
            # area. The downside is that tags created by friends that have a
            # low score may be missed.
            "$limit": limit_friends
            }, {

            # reduce fields (for performance) and create the dynamic field 
            # `is_friend` which indicates whether the content was created by
            # a Facebook friend of the user issuing the request
            "$project": {
                "_id":                  1, 
                "user_id":              1,
                "loc":                  1,
                "text":                 1,
                "url":                  1,
                "score.overall":        1,
                "score.vote":           1,
                "score.day_offset":     1,
                "score.week_offset":    1,
                "score.friend":         {"$cond": [is_friend_cond, 1, 0]},
                }
            }, {
          
            # create intermediate values necessary for recalculating the 
            # overall score to include the friend score
            "$project": {
                "_id":                  1, 
                "user_id":              1,
                "loc":                  1,
                "text":                 1,
                "url":                  1,
                "score.vote":           1,
                "score.day_offset":     1,
                "score.week_offset":    1,
                "score.friend":         1,

                "tmp.score_vote_weighted": {"$multiply": 
                    ["$score.vote",         weights["vote"]]},
                "tmp.score_day_offset_weighted": {"$multiply": 
                    ["$score.day_offset",   weights["day_offset"]]},
                "tmp.score_week_offset_weighted": {"$multiply": 
                    ["$score.week_offset",  weights["week_offset"]]},
                "tmp.score_friend_weighted": {"$multiply": 
                    ["$score.friend",       weights["friend"]]},

                },
            }, {

            # recalculate the overall score
            "$project": {
                "_id":                  1, 
                "user_id":              1,
                "loc":                  1,
                "text":                 1,
                "url":                  1,
                "score.vote":           1,
                "score.day_offset":     1,
                "score.week_offset":    1,
                "score.friend":         1,

                "score.overall": {
                    "$add": [
                        "$tmp.score_vote_weighted",
                        "$tmp.score_day_offset_weighted",
                        "$tmp.score_week_offset_weighted",
                        "$tmp.score_friend_weighted",
                        ]
                    },
                },
            }, {

            # sort by updated score field
            "$sort": {
                "score.overall": -1
                }
            }, {

            # limit the amount of content returned
            "$limit": limit_final

            }
            ]

        result = yield motor.Op(self._conn.aggregate, spec)
        raise tornado.gen.Return(result["result"])


    # OLD (for benchmarking) ---------------------------------------------------

    @tornado.gen.coroutine
    def get_nearby_old(self, lng, lat, limit):
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
        cursor = self._conn.find(spec).limit(limit)
        result = yield motor.Op(cursor.to_list)
        raise tornado.gen.Return(result)


    # --------------------------------------------------------------------------

    @tornado.gen.coroutine
    def put(self, user_id, text, url, accuracy, lng, lat):
        """Save new content to the database."""
        content_id = ObjectId()
        doc = {
            "_id":                  content_id, 
            "created":              long(time.time()),
            "user_id":              user_id,
            "text":                 text,
            "url":                  url,
            "accuracy":             accuracy, # meters
            "loc": {
                "type":             "Point",
                "coordinates":      [lng, lat],
                },
            "votes": {
                "up":               0,
                "down":             0,
                },
            "score": {
                "overall":          0,
                "vote":             0,
                "day_offset":       0,
                "week_offset":      0,
                },
            }
        yield motor.Op(self._conn.insert, doc)
        raise tornado.gen.Return(content_id)

    @tornado.gen.coroutine
    def inc_vote(self, content_id, vote):
        """Increment either the votes up or down count for the content."""
        assert vote in [Vote.UP, Vote.DOWN]
        field = 'votes.up' if vote == Vote.UP else 'votes.down'
        yield motor.Op(
            self._conn.update, {'_id': content_id}, {'$inc': {field: 1}}) 

    @tornado.gen.coroutine
    def exists(self, content_id):
        """Return whether a content ID exists."""
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/
        count = yield motor.Op(
            self._conn.find({'_id': content_id}, {'_id': 1}).limit(1).count)
        raise tornado.gen.Return(count == 1)

