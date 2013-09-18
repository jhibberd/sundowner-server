"""Pick a random point within the Kuala Lumpur geographical bounds and issue
a request for relevant content.

If running this script locally an SSH tunnel will need to be established to the
matador box for mongoDB connectivity:

    ssh -f matador -L 27018:matador:27017 -N

"""

import pprint
import pymongo
import sundowner.data
import sundowner.data.content
import sundowner.ranking
import sys
import time
import random


# see instagram-bot for an explanation of what these values represent
GEO_BOUNDS_WEST_LNG =   101.517105 
GEO_BOUNDS_EAST_LNG =   101.809616
GEO_BOUNDS_NORTH_LAT =  3.219809
GEO_BOUNDS_SOUTH_LAT =  2.876972
rand_lng = random.uniform(GEO_BOUNDS_WEST_LNG, GEO_BOUNDS_EAST_LNG)
rand_lat = random.uniform(GEO_BOUNDS_NORTH_LAT, GEO_BOUNDS_SOUTH_LAT)

# query the content database with the random location
sundowner.data.connect(port=27018)
content = sundowner.data.content.Data.get_nearby(rand_lng, rand_lat)

# define target vector
# votes values are set as 0 because the delta function for calculating the
# vote distance always compares the content's vote score against 1 (the best
# vote score)
now = long(time.time())
target_vector = (
    rand_lng,       # longitude 
    rand_lat,       # latitude
    now,            # created time
    0,              # votes up
    0,              # votes down
    )

top = sundowner.ranking.top(content, target_vector, n=10)

result = {
    'content_count':    len(content),
    'random_location':  (rand_lng, rand_lat),
    'top_content':      top,
    }
pprint.pprint(result)

