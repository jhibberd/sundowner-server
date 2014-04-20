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
RECIPIENTS = {"James", "Annie"}

class RequestHandlerBase(tornado.web.RequestHandler):

    def complete(self, data=None, status_code=httplib.OK):
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

    def _get_json_request_body(self):
        try:
            return json.loads(self.request.body)
        except (ValueError, TypeError):
            raise Exception("Badly formed JSON in the request body.")


class TagsHandler(RequestHandlerBase):

    _MAX_TAGS_PER_ZONE = 20 # iOS geofence limit
    _ZONE_RADIUS = 1000
    _EARTH_RADIUS = 6371000
    _ZONE_RADIUS_RADIANS = float(_ZONE_RADIUS) / _EARTH_RADIUS

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        """Get top tags within a region, or all tags in the database."""

        user_id = self.get_argument("user_id")
        lat = float(self.get_argument("lat"))
        lng = float(self.get_argument("lng"))
        db = self.settings["db"]

        # return top tags in the region
        spec = {
            "loc": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], self._ZONE_RADIUS_RADIANS],
                    },
                },
            "recipients": user_id,
            }

        cursor = db.tags.find(spec)
        result = yield cursor.to_list(self._MAX_TAGS_PER_ZONE)

        # format tag data for response
        def fmt(tag):
            return {
                "id":               str(tag["_id"]),
                "text":             tag["text"],
                "lat":              tag["loc"]["coordinates"][1],
                "lng":              tag["loc"]["coordinates"][0],
                "user_id":          tag["user_id"],
                }
        data = map(fmt, result)

        self.complete(data)

    _RECIPIENTS = {"James", "Annie"}
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        """Create a tag."""

        body = self._get_json_request_body()
        lat = float(body["lat"])
        lng = float(body["lng"])
        text = body["text"]
        user_id = body["user_id"]

        tag_id = ObjectId()
        recipients = list(self._RECIPIENTS - {user_id})

        db = self.settings["db"]

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
        yield db.tags.insert(doc)

        self.complete({"tag_id": str(tag_id)})


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

        user_id = self.get_argument("user_id")
        tag_id = ObjectId(tag_id)
        db = self.settings["db"]

        yield db.tags.update(
            {"_id": tag_id}, {"$pull": {"recipients": user_id}})
        self.complete()


def main():

    # connect to the db
    db = motor.MotorClient(DB_HOST, DB_PORT).minitag

    # ensure compound geospatial multikey index exists
    @tornado.gen.coroutine
    def setup_index():
        yield db.tags.ensure_index(
            [("loc", pymongo.GEOSPHERE), ("recipient", pymongo.ASCENDING)])
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


