"""Run the Sundowner API server.

Usage:

    python main.py path-to-config

"""

import httplib
import json
import sundowner.config
import sundowner.data
import sys
import time
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.web
from bson.objectid import ObjectId
from operator import itemgetter
from sundowner.data.votes import Vote


# Helpers ----------------------------------------------------------------------

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
            'meta': {
                'error_type':       exception.__class__.__name__,
                'code':             status_code,
                'error_message':    exception.message,
                }})

    def complete(self, status_code=httplib.OK, data=None):
        """Return data in a consistent JSON format.

        Adopted schema used by Instagram:
        http://instagram.com/developer/endpoints/
        """
        result = {
            'meta': {
                'code': status_code,
                }}
        if data is not None:
            result['data'] = data
        self.set_status(status_code)
        self.write(result)


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

    @tornado.gen.coroutine
    def get(self):
        """Return top content near a location."""

        params = {
            'lng':      self.get_argument('lng'),
            'lat':      self.get_argument('lat'),
            }
        yield self.validate_get_params(params)

        # get all nearby content
        top_content = yield sundowner.data.content.get_nearby(params['lng'], params['lat'])

        # replace user IDs with usernames
        user_ids = map(itemgetter('user_id'), top_content)
        username_map = yield sundowner.data.users.get_usernames(user_ids)

        result = []
        for content in top_content:
            username = username_map[content['user_id']]
            result.append({
                'id':           str(content['_id']),
                'text':         content['text'],
                'url':          content['url'],
                'username':     username,
                })
        self.complete(data=result)

    @tornado.gen.coroutine
    def post(self):
        """Save content to the database."""

        payload =           self.get_json_request_body()
        params = {
            'lng':          payload.get('lng'),
            'lat':          payload.get('lat'),
            'text':         payload.get('text'),
            'user_id':      payload.get('user_id'),
            'accuracy':     payload.get('accuracy'),
            'url':          payload.get('url'),
            }
        yield self.validate_post_params(params)

        yield sundowner.data.content.put({
            'text':             params['text'],
            'url':              params['url'],
            'user_id':          params['user_id'],
            'accuracy':         params['accuracy'], # meters
            'loc': {
                'type':         'Point',
                'coordinates':  [params['lng'], params['lat']],
                },
            'votes': {
                'up':           0,
                'down':         0,
                },
            'score': {
                'overall':      0,
                'vote':         0,
                'day_offset':   0,
                'week_offset':  0,
                },
            })
        self.complete(httplib.CREATED)

    @tornado.gen.coroutine
    def validate_get_params(self, params):

        lng = params['lng']
        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 
        params['lng'] = lng

        lat = params['lat']
        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 
        params['lat'] = lat

    @tornado.gen.coroutine
    def validate_post_params(self, params):

        lng = params['lng']
        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 
        params['lng'] = lng

        lat = params['lat']
        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 
        params['lat'] = lat

        text = params['text']
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
        params['text'] = text

        user_id = params['user_id']
        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument.")
        if not ObjectId.is_valid(user_id):
            raise BadRequestError("'user_id' is not a valid ID.")
        if not (yield sundowner.data.users.exists(user_id)):
            raise BadRequestError("'user_id' does not exist.")

        accuracy = params['accuracy']
        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except ValueError:
                raise BadRequestError("'accuracy' is not a valid radius.")
            # iOS supplied accuracy as a negative value if it's invalid
            if accuracy < 0:
                accuracy = None
            params['accuracy'] = accuracy
        
        url = params['url']
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
            params['url'] = url


class VotesHandler(RequestHandler):

    @tornado.gen.coroutine
    def post(self):
        """Register a vote up or down against a piece of content."""

        payload =           self.get_json_request_body()
        params = {
            'content_id':   payload.get('content_id'),
            'user_id':      payload.get('user_id'),
            'vote':         payload.get('vote'),
            }
        yield self.validate_get_params(params)

        accepted = yield sundowner.data.votes.put(
            params['user_id'], params['content_id'], params['vote'])
        if accepted:
            yield sundowner.data.content.inc_vote(params['content_id'], params['vote'])
            # otherwise the vote has already been places

        status_code = httplib.CREATED if accepted else httplib.OK
        self.complete(status_code)

    @tornado.gen.coroutine
    def validate_get_params(self, params):

        content_id = params['content_id']
        if content_id is None:
            raise BadRequestError("Missing 'content_id' argument.")
        if not ObjectId.is_valid(content_id):
            raise BadRequestError("'content_id' is not a valid ID.")
        if not (yield sundowner.data.content.exists(content_id)):
            raise BadRequestError("'content_id' does not exist.")

        user_id = params['user_id']
        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument.")
        if not ObjectId.is_valid(user_id):
            raise BadRequestError("'user_id' is not a valid ID.")
        if not (yield sundowner.data.users.exists(user_id)):
            raise BadRequestError("'user_id' does not exist.")

        vote = params['vote']
        if vote is None:
            raise BadRequestError("Missing 'vote' argument.")
        if vote not in [Vote.UP, Vote.DOWN]:
            raise BadRequestError("'vote' is not a valid vote type.")


class UsersHandler(RequestHandler):

    @tornado.gen.coroutine
    def post(self):
        """Resolve a Facebook access token to a user ID.
        
        If this is the first time that the system has encountered the Facebook
        user ID associated with the access token then create a new user.
        """

        payload =           self.get_json_request_body()
        params = {
            "access_token": payload.get("access_token"),
            }
        self.validate_post_params(params)

        # validate the access token using the Facebook Graph API and at the
        # same time retrieve data on the user associated with it
        http_client = tornado.httpclient.AsyncHTTPClient()
        url = "https://graph.facebook.com/me?access_token=%s" % \
            params["access_token"]
        try:
            response = yield http_client.fetch(url)
        except tornado.httpclient.HTTPError as e:
            fb_error = json.loads(e.response.body)
            if fb_error["error"]["type"] == "OAuthException":
                raise BadRequestError("'access_token' is not valid.")
            else:
                raise e
        fb_response = json.loads(response.body)

        # attempt to lookup the user in the "users" collection by their
        # Facebook user ID
        fb_user_id = fb_response["id"]
        user_data = yield \
            sundowner.data.users.get_by_facebook_id(fb_user_id)

        # if no user is found created a new user using the user data retrieved
        # from Facebook
        if user_data is None:
            result = yield \
                sundowner.data.users.create_from_facebook_data(fb_response)
            created = True

        # if a user is found extract the native ID and Facebook name
        else:
            result = {
                "id":       user_data["_id"],
                "name":     user_data["facebook"]["name"],
                }
            created = False

        # can't JSON encode ObjectId object
        result["id"] = str(result["id"])

        status_code = httplib.CREATED if created else httplib.OK
        self.complete(status_code, data=result)

    def validate_post_params(self, params):
        access_token = params['access_token']
        if access_token is None:
            raise BadRequestError("Missing 'access_token' argument.")


# Errors -----------------------------------------------------------------------

class BadRequestError(tornado.web.HTTPError):

    def __init__(self, message):
        super(BadRequestError, self).__init__(httplib.BAD_REQUEST)
        self.message = message


# Main -------------------------------------------------------------------------

application = tornado.web.Application([
    (r"/content",   ContentHandler),    # GET, POST
    (r"/votes",     VotesHandler),      # POST
    (r"/users",     UsersHandler),      # POST
    ])

def main():
    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception('No config file specified')
    sundowner.config.init(config_filepath)
    sundowner.data.connect()
    application.listen(sundowner.config.cfg['port'])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

