"""Authenticates requests (by delegating access token validation to Facebook).
"""

import httplib
import json
import redis
import sundowner.config
import sundowner.data
import time
import tornado.gen
import tornado.httpclient
import urllib
from bson.objectid import ObjectId


@tornado.gen.coroutine
def validate(access_token):
    """Validate a Facebook access token and return the associated local user
    ID, creating a new user record if necessary.
    """

    user_id = _Cache.get(access_token)

    # If the access token isn't in the cache then validate it with Facebook
    # and retrieve its metadata. Extract the user ID from the metadata and 
    # query Facebook again for the user metadata. If a record for the user
    # already exists update it with the latest metadata, otherwise create a new
    # record. Finally cache the access token until Facebook expires it.
    if user_id is None:
        access_token_meta = yield FacebookGraphAPI.debug_token(access_token)
        fb_user_id = access_token_meta["user_id"]
        user_meta = yield FacebookGraphAPI.get_user(fb_user_id, access_token)
        user_id = yield _create_or_update_user_record(fb_user_id, user_meta)
        _Cache.put(access_token, user_id, access_token_meta["expiry"])

    raise tornado.gen.Return(user_id)

@tornado.gen.coroutine
def _create_or_upate_user_record(fb_user_id, user_meta):
    user_record = \
        yield sundowner.data.users.read_by_facebook_user_id(fb_user_id)
    if user_record is None:
        user_id = yield sundowner.data.users.create(user_meta)
    else:
        user_record["facebook"] = user_meta
        yield sundowner.data.users.update(user_record)
        user_id = user_record["_id"]
    raise tornado.get.Return(user_id)

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

        raise tornado.gen.Return({
            "user_id":      data["user_id"],
            "expires_at":   data["expires_at"],
            })

    @staticmethod
    @tornado.gen.coroutine
    def get_user(user_id, access_token):
        """Get metadata associated with a Facebook user ID.""" 
        url = "https://graph.facebook.com/%s?%s" % (user_id, urllib.urlencode({
            "access_token": access_token,
            }))
        http_client = tornado.httpclient.AsyncHTTPClient()
        response = yield http_client.fetch(url)
        user_meta = json.loads(response.body)
        raise tornado.gen.Return(user_meta)


class _Cache(object):
    """Cache user IDs by access token."""

    @classmethod
    def get(cls, access_token):
        key = cls._key(access_token)
        user_id = cls._get_conn().get(key)
        if user_id is None:
            return None
        else:
            return ObjectId(user_id)

    @classmethod
    def put(cls, access_token, user_id, expiry):
        key = cls._key(access_token)
        cls._get_conn().set(
            name=   key, 
            value=  str(user_id),                   # from ObjectId
            ex=     (expiry - long(time.time())     # from timestamp to secs
            )

    @classmethod
    def _get_conn(cls):
        # TODO the app only needs a single redis connection as it's 
        # thread-safe, so refactor this once usage of redis expands to other
        # parts of the app
        if not hasattr(cls, "_conn"):
            cls._conn = redis.Redis(
                host=   sundowner.config.cfg["cache-host"],
                port=   sundowner.config.cfg["cache-port"],
                db=     sundowner.config.cfg["cache-db"],
                )
        return cls._conn

    @staticmethod
    def _key(access_token):
        return "%s/%s" % (sundowner.config.cfg["cache-key-auth"], access_token)


class AuthError(Exception): pass

if __name__ == "__main__":
    sundowner.config.init("/home/jhibberd/projects/sundowner/cfg/sandbox.yaml")
    access_token = "CAADETKZBOw4kBAAj5YlOaZB02G7fJx3yKAP2ZAdP6B9JqbbGoOXjG8K7zdc8xbvqVhFuc3nt7LG2K1pmZBgXTx2ZAFA0OWZCMkCJ0JlJ5W8qjjZBRhrveLBTMlJmTG1vVG3s1gsCnAU6MLoQ0IQZAK349yBByHbiSRcRZBoTJDWoZClgiZB8NCoJnYAeeu4XECZBt0oWUSyigbLd1tGRhTHwQZBtH"
    data = FacebookGraphAPI.debug_token(access_token)
    print FacebookGraphAPI.get_user(data["user_id"], access_token) 
    #print FacebookGraphAPI.debug_token("CAACEdEose0cBADOSxMHr9S5pvwIdfyUcIlm72oMC8ZAMwAZAWnO5110nY0myLl1WAsZBNOeSZBGUSqfCTGQoz99mRVX66OhYth2olXPZCRZC4GrBNhBW5bReE1ZAbq0RbhlZBbDuROoiYtXF20X0EP2U6loJnADRWDTzXKDZBlem8o7m67nM3UctlI2jWiAbeXo4ZD")

