import httplib
import json
import motor
import pymongo
import tornado.gen
import tornado.ioloop
import tornado.web
from bson.objectid import ObjectId


API_PORT = 8888
DB_HOST = "ubuntu"
DB_PORT = 27017


# Request Handlers -------------------------------------------------------------

class RequestHandlerBase(tornado.web.RequestHandler):
    """Base class for all request handlers.

    The response envelope schema is adopted from Instagram:
    http://instagram.com/developer/endpoints/
    """

    def complete(self, data=None, status_code=httplib.OK):
        """Return data in response envelope."""
        result = {
            "meta": {
                "code": status_code,
                }}
        if data is not None:
            result["data"] = data
        self.set_status(status_code)
        self.write(result)
        self.finish()

    def write_error(self, status_code, **kwargs):
        """Overridden to return errors and exceptions in response envelope."""

        exception = kwargs["exc_info"][1]

        # hide details of internal server errors from the client
        if not isinstance(exception, tornado.web.HTTPError):
            exception = tornado.web.HTTPError(httplib.INTERNAL_SERVER_ERROR)
            exception.message = "Uh oh, something went horribly wrong."

        code = getattr(exception, "custom_error_code", status_code)
        self.finish({
            "meta": {
                "error_type":       exception.__class__.__name__,
                "code":             code,
                "error_message":    exception.message,
                }})

    @property
    def db(self):
        """Syntactic shortcut for accessing the database connection."""
        return self.settings["db"]


class TagsHandler(RequestHandlerBase):

    _MAX_TAGS_PER_ZONE = 20 # iOS geofence limit
    _ZONE_RADIUS = 1000 # meters
    _EARTH_RADIUS = 6371000 # meters
    _ZONE_RADIUS_RADIANS = float(_ZONE_RADIUS) / _EARTH_RADIUS

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        """Get tags that are close to a location and have a specific user as a
        recipient.

        Close to a location means within the circle whose center is the
        longitude and latitude in the request and whose radius is
        `_ZONE_RADIUS`.
        """

        user_id, lat, lng = TagsRequestValidator.validate_get(self)

        spec = {
            "loc": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], self._ZONE_RADIUS_RADIANS],
                    },
                },
            "recipients": user_id,
            }
        cursor = self.db.tags.find(spec)
        result = yield cursor.to_list(self._MAX_TAGS_PER_ZONE)

        # format tag data for response
        def fmt(tag):
            # TODO: handle missing meta
            meta = Users.get_meta(tag["user_id"])
            return {
                "id":               str(tag["_id"]),
                "text":             tag["text"],
                "lat":              tag["loc"]["coordinates"][1],
                "lng":              tag["loc"]["coordinates"][0],
                "user_id":          tag["user_id"],
                "user_image_url":   meta["user_image_url"],
                }
        data = map(fmt, result)

        self.complete(data)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        """Create a tag."""

        user_id, lat, lng, text = TagsRequestValidator.validate_post(self)
        tag_id = ObjectId()
        recipients = Users.get_friends(user_id)

        doc = {
            "_id":                  tag_id,
            "loc": {
                "type":             "Point",
                "coordinates":      [lng, lat],
                },
            "text":                 text,
            "user_id":              user_id,
            "recipients":           recipients,
            }
        yield self.db.tags.insert(doc)

        data = {"tag_id": str(tag_id)}
        self.complete(data)


class TagHandler(RequestHandlerBase):

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def delete(self, tag_id):
        """Remove a user from being the future recipient of a tag.

        Typically in response to the user having read and acknowledged the tag.

        The return value from the `update` method doesn't indicate whether
        `user_id` was actually in the `recipients` array, so this endpoint
        won't respond with an error if `user_id` isn't a recipient of the tag.
        """

        user_id = TagRequestValidator.validate_delete(self)
        tag_id = ObjectId(tag_id)

        yield self.db.tags.update(
            {"_id": tag_id}, {"$pull": {"recipients": user_id}})

        self.complete()


# Request Validators -----------------------------------------------------------

_MIN_LNG = -180
_MAX_LNG = 180
_MIN_LAT = -90
_MAX_LAT = 90
_MAX_TEXT_LEN = 256

class TagsRequestValidator(object):
    """Validate and format requests to a list of Tag resources."""

    @staticmethod
    def validate_get(handler):

        # user_id
        user_id = handler.get_argument("user_id", None)
        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument")

        # lat
        lat = handler.get_argument("lat", None)
        if lat is None:
            raise BadRequestError("Missing 'lat' argument")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float")
        if not (_MIN_LAT <= lat <= _MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude")

        # lng
        lng = handler.get_argument("lng", None)
        if lng is None:
            raise BadRequestError("Missing 'lng' argument")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float")
        if not (_MIN_LNG <= lng <= _MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude")

        return user_id, lat, lng

    @staticmethod
    def validate_post(handler):

        try:
            body = json.loads(handler.request.body)
        except (ValueError, TypeError):
            raise BadRequestError("Body is invalid JSON")

        # user_id
        user_id = body.get("user_id")
        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument")

        # lat
        lat = body.get("lat")
        if lat is None:
            raise BadRequestError("Missing 'lat' argument")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float")
        if not (_MIN_LAT <= lat <= _MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude")

        # lng
        lng = body.get("lng")
        if lng is None:
            raise BadRequestError("Missing 'lng' argument")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float")
        if not (_MIN_LNG <= lng <= _MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude")

        # text
        text = body.get("text")
        if text is None:
            raise BadRequestError("Missing 'text' argument")
        if not isinstance(text, basestring):
            raise BadRequestError("'text' must be a string")
        text = text.strip()
        if len(text) == 0:
            raise BadRequestError("'text' cannot be empty")
        if len(text) > _MAX_TEXT_LEN:
            raise BadRequestError(
                "'text' cannot exceed %s characters" % _MAX_TEXT_LEN)

        return user_id, lat, lng, text


class TagRequestValidator(object):
    """Validate and format requests to a Tag resource."""

    @staticmethod
    def validate_delete(handler):

        # user_id
        user_id = handler.get_argument("user_id", None)
        if user_id is None:
            raise BadRequestError("Missing 'user_id' argument")

        return user_id


# Errors -----------------------------------------------------------------------

class BadRequestError(tornado.web.HTTPError):

    def __init__(self, message):
        super(BadRequestError, self).__init__(httplib.BAD_REQUEST)
        self.message = message


# Placeholder Structures -------------------------------------------------------

class Users(object):

    _USERS = {"James", "Annie"}
    _META = {
        "James": {
            "user_image_url": "https://graph.facebook.com/james.d.hibberd/picture?width=100&height=100",
            },
        "Annie": {
            "user_image_url": "https://graph.facebook.com/annie.or.kam.fat/picture?width=100&height=100",
            }
        }

    @classmethod
    def get_friends(cls, user_id):
        """Return a list of users who are friends with a specific user."""
        return list(cls._USERS - {user_id})

    @classmethod
    def get_meta(cls, user_id):
        """Return metadata associated with a user."""
        return cls._META.get(user_id, {})


# Main -------------------------------------------------------------------------

def main():

    # connect to MongoDB before starting the Tornado server to avoid IO loop
    # conflicts
    db = motor.MotorClient(DB_HOST, DB_PORT).minitag

    # ensure compound geospatial multikey index exists
    @tornado.gen.coroutine
    def setup_index():
        yield db.tags.ensure_index([
            ("loc", pymongo.GEOSPHERE),
            ("recipient", pymongo.ASCENDING)])
    tornado.ioloop.IOLoop.current().run_sync(setup_index)

    # start listening for HTTP request
    application = tornado.web.Application([
        (r"/tags/?",                  TagsHandler),   # GET, POST
        (r"/tags/([0-9a-f]{24})/?",   TagHandler),    # DELETE
        ],
        db=db,
        debug=True)
    application.listen(API_PORT)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()


