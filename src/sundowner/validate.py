"""Logic for validating HTTP requests.

Validator classes will raise a BadRequestError if an argument fails a
validation test and format argument values where appropriate.
"""

import httplib
import sundowner.data
import tornado.gen
from bson.objectid import ObjectId
from sundowner.data.votes import Vote
from sundowner.error import BadRequestError


# Validators -------------------------------------------------------------------

class ContentHandlerValidator(object):

    def validate_get(self, args):

        lng = args["lng"]
        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 
        args["lng"] = lng

        lat = args["lat"]
        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 
        args["lat"] = lat

    def validate_post(self, args):

        lng = args["lng"]
        if lng is None:
            raise BadRequestError("Missing 'lng' argument.")
        try:
            lng = float(lng)
        except ValueError:
            raise BadRequestError("'lng' must be a float.") 
        if not (MIN_LNG <= lng <= MAX_LNG):
            raise BadRequestError("'lng' is not a valid longitude.") 
        args["lng"] = lng

        lat = args["lat"]
        if lat is None:
            raise BadRequestError("Missing 'lat' argument.")
        try:
            lat = float(lat)
        except ValueError:
            raise BadRequestError("'lat' must be a float.") 
        if not (MIN_LAT <= lat <= MAX_LAT):
            raise BadRequestError("'lat' is not a valid latitude.") 
        args["lat"] = lat

        text = args["text"]
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
        args["text"] = text

        accuracy = args["accuracy"]
        if accuracy is not None:
            try:
                accuracy = float(accuracy)
            except ValueError:
                raise BadRequestError("'accuracy' is not a valid radius.")
            # iOS supplied accuracy as a negative value if it's invalid
            if accuracy < 0:
                accuracy = None
            args["accuracy"] = accuracy
        
        url = args["url"]
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
            args["url"] = url


class VotesHandlerValidator(object):

    @tornado.gen.coroutine
    def validate_get(self, args):

        content_id = args["content_id"]
        if content_id is None:
            raise BadRequestError("Missing 'content_id' argument.")
        if not ObjectId.is_valid(content_id):
            raise BadRequestError("'content_id' is not a valid ID.")
        content_id = ObjectId(content_id)
        if not (yield sundowner.data.content.exists(content_id)):
            raise BadRequestError("'content_id' does not exist.")
        args["content_id"] = content_id

        vote = args["vote"]
        if vote is None:
            raise BadRequestError("Missing 'vote' argument.")
        if vote not in [Vote.UP, Vote.DOWN]:
            raise BadRequestError("'vote' is not a valid vote type.")


# Constants --------------------------------------------------------------------

MIN_LNG =       -180 
MAX_LNG =       180
MIN_LAT =       -90
MAX_LAT =       90
MAX_TEXT_LEN =  256
MAX_URL_LEN =   2048 # http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers

