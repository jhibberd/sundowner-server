"""Run the Sundowner API server.

Usage:

    python main.py path-to-config

"""

import httplib
import json
import sundowner.config
import sundowner.data
import sundowner.data.content
import sundowner.data.users
import sundowner.data.votes
import sundowner.ranking
import sys
import time
import tornado.ioloop
import tornado.web
from bson.objectid import ObjectId
from operator import itemgetter
from sundowner.data.votes import Vote


# Helpers ----------------------------------------------------------------------

def _trimdict(d):
    """Remove all entries with a None value."""
    return dict([(k, v) for k,v in d.items() if v is not None])

def _get_target_vector(lng, lat):
    """Return the vector used as a target when scoring the proximity of 
    content.

    Vote values are set to 0 
    Vote values are set as 0 because the delta function for calculating the
    vote distance always compares the content's vote score against 1 (the best
    vote score).
    """
    now = long(time.time())
    return (
        lng,    # longitude 
        lat,    # latitude
        now,    # created time
        0,      # votes up
        0,      # votes down
        )

class RequestHandler(tornado.web.RequestHandler):
    """Custom request handler behaviour."""

    def get_json_request_body(self):
        try:
            return json.loads(self.request.body)
        except ValueError, TypeError:
            raise BadRequestError('Badly formed JSON in the request body.')

    def write_error(self, status_code, **kwargs):
        """Overridden to return errors and exceptions in a consistent JSON 
        format.

        Adopted schema used by Instagram:
        http://instagram.com/developer/endpoints/
        """

        exception = kwargs['exc_info'][1]

        # hide details of internal server errors from the client
        if not isinstance(exception, tornado.web.HTTPError):
            exception = tornado.web.HTTPError(httplib.INTERNAL_SERVER_ERROR)
            exception.message = 'Oops, an error occurred.'

        self.finish({
            'error_type':       exception.__class__.__name__,
            'code':             status_code,
            'error_message':    exception.message,
            })


# Handlers ---------------------------------------------------------------------

# constants for request argument validation
MIN_LNG =       -180 
MAX_LNG =       180
MIN_LAT =       -90
MAX_LAT =       90
MAX_TEXT_LEN =  256

# http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
MAX_URL_LEN =   2048

class ContentHandler(RequestHandler):

    def get(self):
        """Return top content near a location."""

        lng =       self.get_argument('longitude')
        lat =       self.get_argument('latitude')
        user_id =   self.get_argument('user_id')

        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' is not a valid longitude.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 

        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' is not a valid latitude.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 

        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument.")
        if not ObjectId.is_valid(user_id):
            raise BadRequestError("'user_id' is not a valid ID.")
        if not sundowner.data.users.Data.exists(user_id):
            raise BadRequestError("'user_id' does not exist.")

        # get all nearby content
        target_vector = _get_target_vector(lng, lat)
        content = sundowner.data.content.Data.get_nearby(lng, lat)

        # filter content that the user has voted down
        user_votes = sundowner.data.votes.Data.get_user_votes(user_id)
        rule = lambda content: (content['_id'], Vote.DOWN) not in user_votes
        content = filter(rule, content)

        # rank content and return top
        top_content = sundowner.ranking.top(content, target_vector, n=10)

        # replace user IDs with usernames
        user_ids = map(itemgetter('user_id'), top_content)
        username_map = sundowner.data.users.Data.get_usernames(user_ids)

        result = []
        for content in top_content:
            username = username_map[content['user_id']]
            result.append({
                'id':           str(content['_id']),
                'text':         content['text'],
                'url':          content['url'],
                'username':     username,
                })

        self.write({'data': result})

    def post(self):
        """Save content to the database."""
        
        payload =       self.get_json_request_body()
        lng =           payload.get('lng')
        lat =           payload.get('lat')
        text =          payload.get('text')
        user_id =       payload.get('user_id')
        accuracy =      payload.get('accuracy')
        url =           payload.get('url')

        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 

        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 

        if text is None:
            raise BadRequestError("Missing 'text' argument.")
        if not isinstance(text, basestring):
            raise BadRequestError("'text' must be a string.")
        text = text.strip()
        if len(text) == 0:
            raise BadRequestError("'text' cannot be empty.")
        if len(text) > MAX_TEXT_LEN:
            raise BadRequestError(
                "'text' cannot exceed %s characters." % MAX_TEXT_LEN)

        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument.")
        if not ObjectId.is_valid(user_id):
            raise BadRequestError("'user_id' is not a valid ID.")
        if not sundowner.data.users.Data.exists(user_id):
            raise BadRequestError("'user_id' does not exist.")

        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except ValueError:
                raise BadRequestError("'accuracy' is not a valid radius.")
            # iOS supplied accuracy as a negative value if it's invalid
            if accuracy < 0:
                accuracy = None
            
        if url is not None:
            if not isinstance(url, basestring):
                raise BadRequestError("'url' must be a string.")
            url = url.strip()
            if len(url) == 0:
                raise BadRequestError("'url' cannot be empty.")
            if len(url) > MAX_URL_LEN:
                raise BadRequestError(
                    "'url' cannot exceed %s characters." % MAX_URL_LEN)
            # currently no regex validation or HTTP checking validation is
            # performed on the URL

        sundowner.data.content.Data.put({
            'text':             text,
            'url':              url,
            'user_id':          user_id,
            'accuracy':         accuracy, # meters
            'loc': {
                'type':         'Point',
                'coordinates':  [lng, lat],
                }
            })


class VotesHandler(RequestHandler):

    def post(self):
        """Register a vote up or down against a piece of content."""

        payload =       self.get_json_request_body()
        content_id =    payload.get('content_id')
        user_id =       payload.get('user_id')
        vote =          payload.get('vote')

        if content_id is None:
            raise BadRequestError("Missing 'content_id' argument.")
        if not ObjectId.is_valid(content_id):
            raise BadRequestError("'content_id' is not a valid ID.")
        if not sundowner.data.content.Data.exists(content_id):
            raise BadRequestError("'content_id' does not exist.")

        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument.")
        if not ObjectId.is_valid(user_id):
            raise BadRequestError("'user_id' is not a valid ID.")
        if not sundowner.data.users.Data.exists(user_id):
            raise BadRequestError("'user_id' does not exist.")

        if vote is None:
            raise BadRequestError("Missing 'vote' argument.")
        if vote not in [Vote.UP, Vote.DOWN]:
            raise BadRequestError("'vote' is not a valid vote type.")

        success = sundowner.data.votes.Data.put(user_id, content_id, vote)
        if success:
            sundowner.data.content.Data.inc_vote(content_id, vote)
        else:
            # the vote has already been placed; silently fail
            pass


# Errors -----------------------------------------------------------------------

class BadRequestError(tornado.web.HTTPError):

    def __init__(self, message):
        super(BadRequestError, self).__init__(httplib.BAD_REQUEST)
        self.message = message


# Main -------------------------------------------------------------------------

application = tornado.web.Application([
    (r'/content',   ContentHandler),   # GET, POST
    (r'/votes',     VotesHandler),     # POST
    ])

def main():
    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception('no config file specified')
    sundowner.config.init(config_filepath)
    sundowner.data.connect()
    application.listen(sundowner.config.cfg['port'])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

