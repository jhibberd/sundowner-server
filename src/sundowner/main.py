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

        user_id = yield auth.validate(self.get_argument("access_token"))
        args = {
            "lng":      self.get_argument("lng"),
            "lat":      self.get_argument("lat"),
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
            user_id, args["lng"], args["lat"])

        self.complete(data=result)

    @tornado.gen.coroutine
    def post(self):
        """Save content to the database."""

        user_id = yield auth.validate(self.get_argument("access_token"))

        payload =           self.get_json_request_body()
        args = {
            "lng":          payload.get("lng"),
            "lat":          payload.get("lat"),
            "text":         payload.get("text"),
            "accuracy":     payload.get("accuracy"),
            "url":          payload.get("url"),
            }
        validate.ContentHandlerValidator().validate_post(args)

        content_id = ObjectId()
        yield sundowner.data.content.put({
            "_id":              content_id, 
            "text":             args["text"],
            "url":              args["url"],
            "user_id":          user_id,
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
            user_id, content_id)

        self.complete(httplib.CREATED)


class VotesHandler(RequestHandler):

    @tornado.gen.coroutine
    def post(self):
        """Register a vote up or down against a piece of content."""

        user_id = yield auth.validate(self.get_argument("access_token"))

        payload =           self.get_json_request_body()
        args = {
            "content_id":   payload.get("content_id"),
            "vote":         payload.get("vote"),
            }
        yield validate.VotesHandlerValidator().validate_get(args)

        accepted = yield sundowner.data.votes.put(
            user_id, args["content_id"], args["vote"])
        if accepted:
            yield sundowner.data.content.inc_vote(
                args["content_id"], args["vote"])
            # otherwise the vote has already been placed

        # write activity
        if args["vote"] == Vote.UP:
            self.settings["activity_pub"].write_user_like_content(
                user_id, args["content_id"])
        else: # already validated so only logical alternative
            self.settings["activity_pub"].write_user_dislike_content(
                user_id, args["content_id"])

        status_code = httplib.CREATED if accepted else httplib.OK
        self.complete(status_code)


# Main -------------------------------------------------------------------------

def main():

    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception("No config file specified")
    sundowner.config.init(config_filepath)
    sundowner.data.connect()

    application = tornado.web.Application([
        (r"/content",   ContentHandler),    # GET, POST
        (r"/votes",     VotesHandler),      # POST
        ], 
        activity_pub=ActivityPub())
    application.listen(sundowner.config.cfg["api-port"])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

