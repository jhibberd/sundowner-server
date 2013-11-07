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

    def validate_get(self, params):

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
    def validate_post(self, params):

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


class VotesHandlerValidator(object):

    @tornado.gen.coroutine
    def validate_get(self, params):

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


class UsersHandlerValidator(object):

    def validate_post(self, params):
        access_token = params['access_token']
        if access_token is None:
            raise BadRequestError("Missing 'access_token' argument.")


# Constants --------------------------------------------------------------------

MIN_LNG =       -180 
MAX_LNG =       180
MIN_LAT =       -90
MAX_LAT =       90
MAX_TEXT_LEN =  256
MAX_URL_LEN =   2048 # http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers

