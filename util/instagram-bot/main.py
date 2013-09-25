"""Populate the Sundowner dataset with Instagram pictures taken in and around
Kuala Lumpur.

Picture requests are made to Instagram's servers in a random manner to avoid
being interpreted as a crawer and having access revoked.

Instagram has a rate limit of 5000 requests per hour:
http://instagram.com/developer/endpoints/

An average content document in mongoDB is ~ 350 bytes:
> Object.bsonsize({
    "username": "xcoffeeaddictionx", 
    "loc": {"type": "Point", "coordinates": [101.717279638, 3.02801739]}, 
    "votes": [0, 0], 
    "title": "Green Tea Latte @ RM 8.90", 
    "url": "http://distilleryimage4.s3.amazonaws.com/86d663ba1b5211e3852e22000ae90903_7.jpg", 
    "created": 1378952701, 
    "_id": "7a935e25f5f1974a5be03d602c855512"})
322

The server storing this data can allocate 20GB which means that roughly
60 million pieces of content can be stored.

"""

import hashlib
import httplib
import pymongo
import random
import requests
import sundowner.data.users
import time
from bson.objectid import ObjectId


INSTAGRAM_CLIENT_ID =       '4eb50b52fa2041dd9f14ef062a27313b'
INSTAGRAM_CLIENT_SECRET =   '554aba96c81743b597f2280fc0b02221' # not needed
INSTAGRAM_ENDPOINT =        'https://api.instagram.com/v1/media/search'

# Requests to Instagram are made within the geographical bounds of Kuala
# Lumpur. The target area is a square bounded north by the Batu Caves, west by
# Shah Alam, south by Putrajaya, and east by Semenyih.
# http://itouchmap.com/latlong.html
GEO_BOUNDS_WEST_LNG =   101.517105 
GEO_BOUNDS_EAST_LNG =   101.809616
GEO_BOUNDS_NORTH_LAT =  3.219809
GEO_BOUNDS_SOUTH_LAT =  2.876972

CAPTION_REPLACEMENT =   'No caption :('
CAPTION_MAX_LEN =       256

def convert(media):
    """Convert Instagram media to Sundowner content.

    Only Instagram media of type 'image' are converted, the rest are returned
    as None, which get filtered later.
    """

    if media['type'] != 'image':
        return None

    # hash the image ID to a 24 byte hexadecimal string to simluate an ObjectId
    # but prevent duplicates being stored (as it's deterministic)
    m = hashlib.md5()
    m.update(media['id'])
    doc_id = ObjectId(m.hexdigest()[:24])

    # image caption is optional so provide replacement
    def format_caption():
        """Sometimes the caption doesn't exist and sometimes it does but it's
        too long. Handle all that by always returning an acceptable string.
        """
        caption = media['caption']
        if caption is None:
            return CAPTION_REPLACEMENT
        caption_text = caption['text']
        if len(caption_text) <= CAPTION_MAX_LEN:
            return caption_text
        return caption_text[:CAPTION_MAX_LEN] + '...'

    username = media['user']['username']
    user_id = sundowner.data.users.Data.get_id(
        username, create_if_not_found=True)

    # not sure why Instagram express Unix timestamps as strings
    created =   long(media['created_time'])
    lng =       media['location']['longitude']
    lat =       media['location']['latitude']
    url =       media['images']['standard_resolution']['url']
    votes_up =  media['likes']['count']
    text =      format_caption()

    return {
        '_id':              doc_id,
        'user_id':          user_id,
        'created':          created,
        'url':              url,
        'votes':            {'up': votes_up, 'down': 0},
        'text':             text,

        # location is expressed using GeoJSON to maxke use of mongoDB's 
        # geospatial index
        'loc': {
            'type':         'Point',
            'coordinates':  [lng, lat],
            },
        }

def request(content_collection):
    """Issue a single HTTP request to Instagram for media data associated with
    a random geographical location within the predefined bounds.
    """

    rand_lng = random.uniform(GEO_BOUNDS_WEST_LNG, GEO_BOUNDS_EAST_LNG)
    rand_lat = random.uniform(GEO_BOUNDS_NORTH_LAT, GEO_BOUNDS_SOUTH_LAT)

    # pictures returned are those taken in the last 5 days
    # http://instagram.com/developer/endpoints/media/
    payload = {
        'lng':          rand_lng,
        'lat':          rand_lat,
        'distance':     5000, # 5km, the max
        'client_id':    INSTAGRAM_CLIENT_ID,
        }
    response = requests.get(INSTAGRAM_ENDPOINT, params=payload)

    # if the server returns a Gateway Timeout response then wait for a short
    # while before before trying again (the Instagram server is probably just
    # busy)
    if response.status_code == httplib.GATEWAY_TIMEOUT:
        print 'Gateway Timeout'
        time.sleep(10)
        return

    # similarly if the server returns a Bad Gateway response (which happens
    # from time to time) wait for a short while then try again
    elif response.status_code == httplib.BAD_GATEWAY:
        print 'Bad Gateway'
        time.sleep(5)
        return

    # if the server returns a Service Unavailable response then it looks like
    # we've been rate limited so wait for a slightly longer period of time
    # before continuing
    elif response.status_code == httplib.SERVICE_UNAVAILABLE:
        print 'Service Unavailable'
        time.sleep(1800) # 30 mins
        return

    # from time to time it happens
    elif response.status_code == httplib.INTERNAL_SERVER_ERROR:
        print 'Internal Server Error'
        time.sleep(1800) # 30 mins
        return

    # if there's a different error response just stop the script so the error 
    # message can be manually examined
    elif response.status_code != httplib.OK:
        raise Exception((response.status_code, response.text))

    media = response.json()['data']
    content = filter(None, map(convert, media))
    map(content_collection.save, content)


if __name__ == '__main__':

    conn = pymongo.MongoClient().sundowner_instagram
    sundowner.data.users.Data.init(conn)
    # this collection needs a geospatial index
    content_collection = conn.content

    while True:
        request(content_collection)

        # wait a random amount of time between requests to avoid Instagram
        # from interpreting our requests as crawl attempts. The average wait
        # is 1 second which (if each request was processed in 0 seconds)
        # would result in 3600 requests per hour. The limit is 5000 so the
        # script should remain well under this limit.
        time.sleep(random.uniform(0.5, 1.5))

