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
from sundowner import memsort, validate
from sundowner.analytics.activity.pub import ActivityPub
from sundowner.data.votes import Vote
from sundowner.error import BadRequestError


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

class ContentHandler(RequestHandler):

    _RESULT_SIZE = 10
    @tornado.gen.coroutine
    def get(self):
        """Return top content near a location."""

        args = {
            "lng":      self.get_argument("lng"),
            "lat":      self.get_argument("lat"),
            "user_id":  self.get_argument("user_id"),
            }
        validate.ContentHandlerValidator().validate_get(args)

        # get all nearby content
        top_content = yield sundowner.data.content.get_nearby(
            args["lng"], args["lat"])

        # refine sort order be performing secondary, in-memory sort using
        # additional content attributes
        top_content = memsort.sort(args["lng"], args["lat"], top_content)
        top_content = top_content[:self._RESULT_SIZE]

        # replace user IDs with usernames
        user_ids = map(itemgetter("user_id"), top_content)
        username_map = yield sundowner.data.users.get_usernames(user_ids)

        result = []
        for content in top_content:
            username = username_map[content["user_id"]]
            result.append({
                "id":           str(content["_id"]),
                "text":         content["text"],
                "url":          content["url"],
                "username":     username,
                })

        # write activity
        self.settings["activity_pub"].write_user_view_content(
            args["user_id"], args["lng"], args["lat"])

        self.complete(data=result)

    @tornado.gen.coroutine
    def post(self):
        """Save content to the database."""

        payload =           self.get_json_request_body()
        args = {
            "lng":          payload.get("lng"),
            "lat":          payload.get("lat"),
            "text":         payload.get("text"),
            "user_id":      payload.get("user_id"),
            "accuracy":     payload.get("accuracy"),
            "url":          payload.get("url"),
            }
        yield validate.ContentHandlerValidator().validate_post(args)

        content_id = ObjectId()
        yield sundowner.data.content.put({
            "_id":              content_id, 
            "text":             args["text"],
            "url":              args["url"],
            "user_id":          args["user_id"],
            "accuracy":         args["accuracy"], # meters
            "loc": {
                "type":         "Point",
                "coordinates":  [args["lng"], args["lat"]],
                },
            "votes": {
                "up":           0,
                "down":         0,
                },
            "score": {
                "overall":      0,
                "vote":         0,
                "day_offset":   0,
                "week_offset":  0,
                },
            })

        # write activity
        self.settings["activity_pub"].write_user_create_content(
            args["user_id"], content_id)

        self.complete(httplib.CREATED)


class VotesHandler(RequestHandler):

    @tornado.gen.coroutine
    def post(self):
        """Register a vote up or down against a piece of content."""

        payload =           self.get_json_request_body()
        args = {
            "content_id":   payload.get("content_id"),
            "user_id":      payload.get("user_id"),
            "vote":         payload.get("vote"),
            }
        yield validate.VotesHandlerValidator().validate_get(args)

        accepted = yield sundowner.data.votes.put(
            args["user_id"], args["content_id"], args["vote"])
        if accepted:
            yield sundowner.data.content.inc_vote(
                args["content_id"], args["vote"])
            # otherwise the vote has already been places

        # write activity
        if args["vote"] == Vote.UP:
            self.settings["activity_pub"].write_user_like_content(
                args["user_id"], args["content_id"])
        else: # already validated so only logical alternative
            self.settings["activity_pub"].write_user_dislike_content(
                args["user_id"], args["content_id"])

        status_code = httplib.CREATED if accepted else httplib.OK
        self.complete(status_code)


class UsersHandler(RequestHandler):

    @tornado.gen.coroutine
    def post(self):
        """Resolve a Facebook access token to a user ID.
        
        If this is the first time that the system has encountered the Facebook
        user ID associated with the access token then create a new user.
        """

        payload =           self.get_json_request_body()
        args = {
            "access_token": payload.get("access_token"),
            }
        validate.UsersHandlerValidator().validate_post(args)

        # validate the access token using the Facebook Graph API and at the
        # same time retrieve data on the user associated with it
        http_client = tornado.httpclient.AsyncHTTPClient()
        url = "https://graph.facebook.com/me?access_token=%s" % \
            args["access_token"]
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


# Main -------------------------------------------------------------------------

def main():

    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception('No config file specified')
    sundowner.config.init(config_filepath)
    sundowner.data.connect()

    application = tornado.web.Application([
        (r"/content",   ContentHandler),    # GET, POST
        (r"/votes",     VotesHandler),      # POST
        (r"/users",     UsersHandler),      # POST
        ], 
        activity_pub=ActivityPub())
    application.listen(sundowner.config.cfg['port'])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

