"""Run the Sundowner API server.

Usage:

    python main.py path-to-config

"""

import httplib
import json
import sundowner.auth
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
from sundowner import validate
from sundowner.analytics.activity.pub import ActivityPub
from sundowner.data.votes import Vote
from sundowner.error import BadRequestError
from sundowner.model.content import ContentModel


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

        code = getattr(exception, "custom_error_code", status_code)
        self.finish({
            "meta": {
                "error_type":       exception.__class__.__name__,
                "code":             code,
                "error_message":    exception.message,
                }})

    def complete(self, status_code=httplib.OK, data=None):
        """Return data in a consistent JSON format.

        Adopted schema used by Instagram:
        http://instagram.com/developer/endpoints/
        """
        result = {
            "meta": {
                "code": status_code,
                }}
        if data is not None:
            result["data"] = data
        self.set_status(status_code)
        self.write(result)
        self.finish()


# Handlers ---------------------------------------------------------------------

class ContentHandler(RequestHandler):

    _RESULT_SIZE = 10
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        """Return top content near a location."""

        args = {
            "access_token":     self.get_argument("access_token"),
            "lng":              self.get_argument("lng"),
            "lat":              self.get_argument("lat"),
            }
        user_id = yield sundowner.auth.validate(args["access_token"])
        validate.ContentHandlerValidator().validate_get(args)

        # get all nearby content
        result = yield ContentModel.get_nearby(
            args["lng"], args["lat"], user_id)

        # write activity
        self.settings["activity_pub"].write_user_view_content(
            user_id, args["lng"], args["lat"])

        self.complete(data=result)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        """Save content to the database."""

        payload =               self.get_json_request_body()
        args = {
            "access_token":     payload.get("access_token"),
            "text":             payload.get("text"),
            "url":              payload.get("url"),
            "accuracy":         payload.get("accuracy"),
            "lng":              payload.get("lng"),
            "lat":              payload.get("lat"),
            }
        user_id = yield sundowner.auth.validate(args["access_token"])
        validate.ContentHandlerValidator().validate_post(args)

        # write content to db
        content_id = yield sundowner.data.content.put(
            user_id, 
            args["text"], 
            args["url"], 
            args["accuracy"], 
            args["lng"], 
            args["lat"])

        # write activity
        self.settings["activity_pub"].write_user_create_content(
            user_id, content_id)

        self.complete(httplib.CREATED)


class VotesHandler(RequestHandler):

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        """Register a vote up or down against a piece of content."""

        payload =               self.get_json_request_body()
        args = {
            "access_token":     payload.get("access_token"),
            "content_id":       payload.get("content_id"),
            "vote":             payload.get("vote"),
            }
        user_id = yield sundowner.auth.validate(args["access_token"])
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

