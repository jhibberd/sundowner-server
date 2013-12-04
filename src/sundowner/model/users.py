import sundowner.data
import tornado.gen
from operator import itemgetter
from sundowner.cache.friends import FriendsCache


class UsersModel(object):

    @staticmethod
    @tornado.gen.coroutine
    def get_friends(user_id):
        """Return the list of Facebook friends of user `user_id` who are also 
        using the service.

        The friends list is a list of native user IDs (not Facebook user IDs),
        each an object of type ObjectId.

        A caching layer sits before the database.
        """

        result = FriendsCache.get(user_id)
        if result is None:

            user = yield sundowner.data.users.read(user_id)
            try:
                fb_friends = user["facebook"]["friends"]["data"]
            except KeyError:
                # I don't think it's possible that this path in the user's data
                # wouldn't exist but if it doesn't, log it so that it can be 
                # investigated
                print "Facebook user with no/unexpected friends data"
                fb_friends = []

            fb_user_ids = map(itemgetter("id"), fb_friends)
            result = yield sundowner.data.users.\
                read_native_user_ids_from_facebook_user_ids(fb_user_ids)
            FriendsCache.put(user_id, result)

        raise tornado.gen.Return(result)

