import datetime
import sundowner.data.content
from math import radians, cos, sin, asin, sqrt


_SECONDS_PER_DAY =      86400
_SECONDS_PER_WEEK =     604800

# prepared vector indices
_LNG =           0
_LAT =           1
_DAY_OFFSET =    5
_WEEK_OFFSET =   6
_VOTE_SCORE =    7

_WEIGHT_VECTOR = [
    1.0,    # geographical distance
    0.3,    # day offset
    0.1,    # week offset
    0.8,    # vote score
    ]

def top(content_list, target_vector, n):
    """Return the top n content ranked by proximity to the target vector."""

    # prepare the target vector once
    prep_target_vector = _prepare_vector(target_vector)

    # calculate the score for each piece of content
    scores = []
    for i, content in enumerate(content_list):
        vector = _to_vector(content)
        prep_vector = _prepare_vector(vector)
        delta_vector = _compare_vectors(prep_vector, prep_target_vector)
        score = _score(delta_vector)
        scores.append((score, i))

    # sort the content indices by score
    scores.sort(reverse=True)

    # create an array of the top content
    top_content = []
    for _, i in scores[:n]:
        top_content.append(content_list[i])

    # add the proximity data to make it easier to tweak the algorithm
    _add_proximity_data(top_content, prep_target_vector)

    return top_content

def _to_vector(content):
    """Extract the salient fields from a content dict and express as a vector.
    """
    lng, lat =              content['loc']['coordinates']
    vote_up, vote_down =    content.get('votes', (0, 0))
    created =               content['created']
    return (lng, lat, created, vote_up, vote_down)

def _prepare_vector(vector):
    """Augment the vector with additional values derived from the original 
    values. These additional values are used multiple times by the delta
    functions, so this preparation avoids the same values from being repeatedly
    computed.
    """
    _, _, created, vote_up, vote_down = vector
    day_offset =    created % _SECONDS_PER_DAY
    week_offset =   created % _SECONDS_PER_WEEK
    vote_score =    _wilson_score_interval(vote_up, vote_down)
    return vector + (day_offset, week_offset, vote_score)

def _compare_vectors(content_vector, target_vector):
    """For each dimension apply the delta function to the content and target
    (prepared) vectors to get a distance (delta) score which represents the
    proximity of the content to the target. The result is a delta vector.
    """
    return map(lambda f: f(content_vector, target_vector), [
        _delta_location,
        _delta_day_offset,
        _delta_week_offset,
        _delta_votes_score,
        ])

def _score(delta_vector):
    """The score is the dot product of the delta and weight vectors."""
    score = sum(d*w for d,w in zip(delta_vector, _WEIGHT_VECTOR))
    normalised_score = score / sum(_WEIGHT_VECTOR)
    return normalised_score

def _delta_location(c, t):
    """Distance in meters between two points on Earth."""
    return 1 - (_haversine(c[_LNG], c[_LAT], t[_LNG], t[_LAT]) / \
                sundowner.data.content.QUERY_RADIUS)

def _delta_day_offset(c, t):
    """Distance in seconds between two times of day (00:00 - 23:59).
    
    Because the dimension is cyclical (a repeating 24 hour circle) the max
    distance between 2 points is 12 hours (anything greater and the distance to 
    a point in the previous/next day because the shortest.
    """

    shortest_diff = abs(c[_DAY_OFFSET] - t[_DAY_OFFSET])
    if shortest_diff > (_SECONDS_PER_DAY / 2):
        shortest_diff = _SECONDS_PER_DAY - shortest_diff 

    proportion_of_day = float(shortest_diff) / (_SECONDS_PER_DAY / 2.0)
    score = 1 - proportion_of_day
    return score

def _delta_week_offset(c, t):
    """Distance in seconds between two times of week (Mon 00:00 - Sun 23:59).

    See '_delta_day_offset'.
    """

    shortest_diff = abs(c[_WEEK_OFFSET] - t[_WEEK_OFFSET])
    if shortest_diff > (_SECONDS_PER_WEEK / 2):
        shortest_diff = _SECONDS_PER_WEEK - shortest_diff 

    proportion_of_week = float(shortest_diff) / (_SECONDS_PER_WEEK / 2.0)
    score = 1 - proportion_of_week
    return score

def _delta_votes_score(c, t):
    """Vote score already represents a normalized distance."""
    return c[_VOTE_SCORE]

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

def _wilson_score_interval(up, down):
    """Given the ratings I have, there is a 95% chance that the "real" fraction 
    of positive ratings is at least what?

    http://stackoverflow.com/questions/10029588/python-implementation-of-the-wilson-score-interval
    http://amix.dk/blog/post/19588
    http://blog.reddit.com/2009/10/reddits-new-comment-sorting-system.html
    http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
    """

    n = up + down
    if n == 0:
        return 0

    z = 1.96 # 95% confidence
    phat = float(up) / n
    return ((phat + z*z/(2*n) - z * sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))

def _add_proximity_data(content_list, prep_target_vector):
    """Add proximity data to each piece of top content to make it clearer to
    a human how the various components of the proximity algorithm are.
    """

    def f(content):

        # recalculate deltas (which is preferrable to maintaining all the 
        # deltas in memory until the top content is determined)
        vector = _to_vector(content)
        prep_vector = _prepare_vector(vector)
        delta_vector = _compare_vectors(prep_vector, prep_target_vector)
        distance, day_offset, week_offset, vote_score = delta_vector

        # create human friendly versions of the day and week offsets
        fmt_created = lambda fmt: \
            datetime.datetime.fromtimestamp(content['created']).strftime(fmt)
        human_day_offset =      fmt_created('%H:%M')
        human_week_offset =     fmt_created('%a')

        # create human friendly geographical distance
        human_distance = '%dm' % _haversine(
            prep_vector[_LNG], prep_vector[_LAT],
            prep_target_vector[_LNG], prep_target_vector[_LAT])

        # recalculate the score
        score = _score(delta_vector)

        content['proximity_data'] = {
            'score':                score,
            'distance': {
                'score':            distance,
                'human_friendly':   human_distance,
                },
            'day_offset': {
                'score':            day_offset, 
                'human_friendly':   human_day_offset,
                },
            'week_offset': {
                'score':            week_offset,
                'human_friendly':   human_week_offset,
                },
            'vote_score':           vote_score,
            }

    map(f, content_list)

