import tornado.gen
import sundowner.config
import sundowner.data
from math import radians, cos, sin, asin, sqrt
from operator import itemgetter
from sundowner.model.users import UsersModel


class ContentModel(object):

    _BATCH_SIZE_DB_FRIENDS =    2000
    _BATCH_SIZE_DB_FINAL =      1000
    _BATCH_SIZE_RESULT =        10

    @classmethod
    @tornado.gen.coroutine
    def get_nearby(cls, lng, lat, user_id):

        # get a list of the user's Facebook friends; tags authored by 
        # friends are ranked higher
        friends = yield UsersModel.get_friends(user_id)

        # Query the database for tags, performing as much of the query 
        # algorithm in the database as possible for efficiency. Returns a list
        # of the highest scoring tags that appears within a query radius.
        tags = yield sundowner.data.content.get_nearby(
            lng, lat, friends, cls._BATCH_SIZE_DB_FRIENDS, 
            cls._BATCH_SIZE_DB_FINAL)

        # Now perform LIGHTWEIGHT manipulation of the database results before
        # they're returned. Only manipulations that couldn't be performed in
        # the database should be done here:

        # allow the tag's distance from the query location to influence the 
        # sort order
        tags = _DistanceSorter.sort(lng, lat, tags, cls._BATCH_SIZE_RESULT)

        # author data for tags not created by friends is not shown, but author 
        # data for tags created by friends needs to be retrieved from the 
        # `Users` collection
        friend_user_ids = []
        for tag in tags:
            if tag["score"]["friend"]:
                friend_user_ids.append(tag["user_id"])
        username_map = \
            yield sundowner.data.users.get_usernames(friend_user_ids)
            
        # format and return the result
        result = []
        for tag in tags:
            entry = {
                "id":       str(tag["_id"]),
                "text":     tag["text"],
                "url":      tag["url"],
                "score":    tag["score"],
                }
            if tag["score"]["friend"]:
                entry["username"] = username_map[tag["user_id"]]
            result.append(entry)
        
        raise tornado.gen.Return(result)


class _DistanceSorter(object):
    """Sort a list of tags by a value that is a combination of the tag's
    distance from a target lng/lat and it's score, then return the top items.
    """

    @classmethod
    def sort(cls, lng, lat, tags, limit):
        """Perform the sort."""
        lst = []
        for tag in tags:
            tag_score =         tag["score"]["overall"]
            tag_lng, tag_lat =  tag["loc"]["coordinates"]
            distance = cls._haversine(tag_lng, tag_lat, lng, lat)
            distance = cls._stand_distance(distance)
            tag["score"]["location"] = distance
            cls._update_overall_score(tag)
            lst.append((tag["score"]["overall"], tag))
        lst.sort(reverse=True)
        return map(itemgetter(1), lst)[:limit]

    @staticmethod
    def _haversine(lgn1, lat1, lgn2, lat2):
        """Calculate the great circle distance between two points on the earth.

        http://en.wikipedia.org/wiki/Haversine_formula
        http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        """
        
        lgn1, lat1, lgn2, lat2 = map(radians, [lgn1, lat1, lgn2, lat2])
        dlgn = lgn2 - lgn1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlgn/2)**2
        c = 2 * asin(sqrt(a)) 
        meters = sundowner.data.content.EARTH_RADIUS * c
        return meters 

    @staticmethod
    def _stand_distance(d):
        """Standardise the distance to a score between 0 - 1."""
        return 1 - (d / sundowner.data.content.QUERY_RADIUS)

    @staticmethod
    def _update_overall_score(tag):
        weights = sundowner.config.cfg["score-weights"]
        score = tag["score"]
        score["overall"] = sum([
            score["vote"] *         weights["vote"],
            score["day_offset"] *   weights["day_offset"],
            score["week_offset"] *  weights["week_offset"],
            score["friend"] *       weights["friend"],
            score["location"] *     weights["location"],
            ])

