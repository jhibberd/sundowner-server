"""Authenticates requests (by delegating access token validation to Facebook).
"""

import httplib
import json
import sundowner.config
import sundowner.data
import time
import tornado.gen
import tornado.httpclient
import urllib
from sundowner.cache.access_token import AccessTokenCache
from sundowner.cache.friends import FriendsCache
from sundowner.error import AuthError


@tornado.gen.coroutine
def validate(access_token):
    """Validate a Facebook access token and return the associated local user
    ID, creating a new user record if necessary.
    """

    user_id = AccessTokenCache.get(access_token)

    # If the access token isn't in the cache then validate it with Facebook
    # and retrieve its metadata. Extract the user ID from the metadata and 
    # query Facebook again for the user metadata. If a record for the user
    # already exists update it with the latest metadata, otherwise create a new
    # record. Finally cache the access token until Facebook expires it.
    #
    # If new user metadata is being retrieved it may contain a different list
    # of friends to those already cached for the user, so clear the user's
    # friends cache.
    if user_id is None:
        access_token_meta = yield FacebookGraphAPI.debug_token(access_token)
        fb_user_id = access_token_meta["user_id"]
        user_meta = yield FacebookGraphAPI.get_user(fb_user_id, access_token)
        user_id = yield \
            _create_or_update_user_record(fb_user_id, user_meta, access_token)
        FriendsCache.clear(user_id)
        AccessTokenCache.put(
            access_token, user_id, access_token_meta["expires_at"])

    raise tornado.gen.Return(user_id)

@tornado.gen.coroutine
def _create_or_update_user_record(fb_user_id, user_meta, access_token):

    user_record = \
        yield sundowner.data.users.read_by_facebook_user_id(fb_user_id)

    if user_record is None:
        user_record = {
            "facebook":                         user_meta,
            "last_facebook_update":             long(time.time()),
            "access_token":                     access_token,

            # This value needs to appear at the top level of the doc so that
            # the `facebook_id` index covers the 
            # `read_native_user_ids_from_facebook_user_ids` query. Is seems
            # that using dot notation prevents MongoDB from covering the 
            # query.
            "facebook_id":                      fb_user_id,
            }
        user_id = yield sundowner.data.users.create(user_record)

    else:
        user_record["facebook"] =               user_meta
        user_record["last_facebook_update"] =   long(time.time())
        user_record["access_token"] =           access_token
        yield sundowner.data.users.update(user_record)
        user_id = user_record["_id"]

    raise tornado.gen.Return(user_id)

class FacebookGraphAPI(object):

    @staticmethod
    @tornado.gen.coroutine
    def debug_token(access_token):
        """Retrieve access token metadata.
        
        https://developers.facebook.com/docs/facebook-login/access-tokens/
        See "Getting Info about Tokens and Debugging"
        """

        app_access_token = "%s|%s" % (
            sundowner.config.cfg["fb-app-id"],
            sundowner.config.cfg["fb-app-secret"])
        url = "https://graph.facebook.com/debug_token?" + urllib.urlencode({
            "input_token":  access_token,
            "access_token": app_access_token,
            })

        http_client = tornado.httpclient.AsyncHTTPClient()
        try:
            response = yield http_client.fetch(url)
        except tornado.httpclient.HTTPError as e:
            # Facebook will return an error if the access token doesn't match
            # the app ID
            response_body = json.loads(e.response.body)
            msg = response_body["error"]["message"]
            raise AuthError(msg)
        else:
            response_body = json.loads(response.body)

        # TODO is it possible that 'is_valid' could be False?
        data = response_body["data"]
        if data["is_valid"] != True:
            raise AuthError("Access token isn't valid")

        # Facebook user IDs are stored as strings in the database
        user_id = str(data["user_id"])

        raise tornado.gen.Return({
            "user_id":      user_id,
            "expires_at":   data["expires_at"],
            })

    @staticmethod
    @tornado.gen.coroutine
    def get_user(user_id, access_token):
        """Get metadata associated with a Facebook user ID.""" 

        # it isn't possible to retrive all default user properties plus their
        # friends list without explicitly listing each user property
        # http://stackoverflow.com/questions/10389364
        # https://developers.facebook.com/docs/graph-api/reference/user/
        # NOTE The friends list is limited to 5000 entries. Retrieving any more
        # than this would require the ability to handle pagination.
        fields = "id,link,first_name,quotes,name,hometown,bio,religion,middle_name,about,is_verified,gender,third_party_id,relationship_status,last_name,locale,verified,political,name_format,significant_other,website,location,username,friends"

        url = "https://graph.facebook.com/%s?%s" % (user_id, urllib.urlencode({
            "fields":       fields,
            "access_token": access_token,
            }))
        http_client = tornado.httpclient.AsyncHTTPClient()
        response = yield http_client.fetch(url)
        user_meta = json.loads(response.body)
        raise tornado.gen.Return(user_meta)

