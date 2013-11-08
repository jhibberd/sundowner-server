import sundowner.data.content
from math import radians, cos, sin, asin, sqrt
from operator import itemgetter


_WEIGHT_SCORE =     0.5
_WEIGHT_DISTANCE =  0.5

def sort(lng, lat, content):
    """Perform a secondary, in-memory sort of the content retrieved from the
    database, which includes attributes that it's not possible to use in a
    database query.

    The attributes being used are:

        * Distance from the target coordinate

    """
    ps = []
    for c in content:
        c_score =       c["score"]["overall"]
        c_lng, c_lat =  c["loc"]["coordinates"]
        distance = _haversine(c_lng, c_lat, lng, lat)
        distance = _stand_distance(distance)
        p = (c_score * _WEIGHT_SCORE) + (distance * _WEIGHT_DISTANCE)
        ps.append((p, c))
    ps.sort()
    return map(itemgetter(1), ps)

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

def _stand_distance(d):
    """Standardise the distance to a score between 0 - 1."""
    return 1 - (d / sundowner.data.content.QUERY_RADIUS)

