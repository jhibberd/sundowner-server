import motor
import pprint
import random
import sundowner.data
import test
import timeit
import tornado.gen
from sundowner.cache.friends import FriendsCache
from sundowner.model.content import ContentModel
from tornado.ioloop import IOLoop


class Test(test.TestBase):

    QUERY_LAT =     0
    QUERY_LNG =     0
    NUM_USERS =     100
    NUM_FRIENDS =   20
    NUM_TAGS =      6000
    NUM_TRIALS =    500

    def test_get_tags(self):

        # SETUP ----------------------------------------------------------------

        # create mock user docs in the database 
        @tornado.gen.coroutine
        def setup_users():
            result = []
            for _ in range(self.NUM_USERS):
                username = self.rand_noun()
                user_id = yield sundowner.data.users.create({
                    "facebook": {
                        "id":   None,
                        "name": username,
                        }})
                result.append(user_id)
            raise tornado.gen.Return(result)
        users = IOLoop.instance().run_sync(setup_users)

        # one of the users will act as the user issuing the request and another
        # subset will act as friends of this user
        friends = random.sample(users, self.NUM_FRIENDS+1)
        user_id = friends.pop()

        # add friends to cache
        FriendsCache.put(user_id, friends)

        # create mock tags
        @tornado.gen.coroutine
        def create_tag():

            # pick a random lng/lat inside the query radius
            # it appears that a lng/lat > (QUERY_RADIUS_RADIANS + .006) will 
            # fall outside the query radius
            qrr = sundowner.data.content._QUERY_RADIUS_RADIANS
            lng = random.uniform(self.QUERY_LNG-qrr, self.QUERY_LNG+qrr)
            lat = random.uniform(self.QUERY_LAT-qrr, self.QUERY_LAT+qrr)
           
            user_id = random.choice(users)
            text = self.rand_noun()

            content_id = yield sundowner.data.content.put(
                user_id=    user_id,
                text=       text,
                url=        None,
                accuracy=   0,
                lng=        lng,
                lat=        lat)

            raise tornado.gen.Return(content_id)

        for _ in range(self.NUM_TAGS):
            IOLoop.instance().run_sync(create_tag)


        # TEST -----------------------------------------------------------------

        def test():
            @tornado.gen.coroutine
            def query_content():
                result = yield ContentModel.get_nearby(
                    self.QUERY_LNG, self.QUERY_LAT, user_id)
                raise tornado.gen.Return(result)
            return IOLoop.instance().run_sync(query_content)
        
        """
        def test_old():
            @tornado.gen.coroutine
            def query_content():
                result = yield ContentModel.get_nearby_old(
                    self.QUERY_LNG, self.QUERY_LAT)
                raise tornado.gen.Return(result)
            result = IOLoop.instance().run_sync(query_content)
        """

        #print "OLD", timeit.timeit(test_old, number=self.NUM_TRIALS)
        #print "NEW", timeit.timeit(test, number=self.NUM_TRIALS)
        pprint.pprint(test())
        raise Exception

