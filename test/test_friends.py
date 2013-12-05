import motor
import sundowner.config
import sundowner.data
import sundowner.model.users
import tornado.gen
import unittest
from bson.objectid import ObjectId
from sundowner.cache import _ThreadSafeCacheConnection
from sundowner.model.users import UsersModel
from tornado.ioloop import IOLoop


class Test(unittest.TestCase):

    # Setup --------------------------------------------------------------------

    _CFG_PATH = "/home/jhibberd/projects/sundowner/cfg/dev.yaml"
    def setUp(self):
        # init and reset env
        sundowner.config.init(self._CFG_PATH)
        sundowner.data.connect()
        self.clear_db()
        _ThreadSafeCacheConnection.get().flushall()

    @classmethod
    def clear_db(cls):
        @tornado.gen.coroutine
        def f():
            yield motor.Op(sundowner.data.users._conn.remove, None)
        IOLoop.instance().run_sync(f)


    # Tests --------------------------------------------------------------------

    def test_get_friends(self):

        # native and Facebook IDs for some friends
        bill = ObjectId()
        jane = ObjectId()
        pete = ObjectId()
        bill_fb = "a"
        jane_fb = "b"
        pete_fb = "c"

        # a Facebook friend who isn't a user
        john_fb = "d"

        @tornado.gen.coroutine
        def seed_db(): 
            yield motor.Op(sundowner.data.users._conn.insert, [
                {"_id": bill, "facebook_id": bill_fb},
                {"_id": jane, "facebook_id": jane_fb},
                {"_id": pete, "facebook": {"friends": {"data": [
                    {"id": bill_fb},
                    {"id": john_fb},
                    {"id": jane_fb},
                    ]}}},
                ])

        @tornado.gen.coroutine
        def test():
            result = yield UsersModel.get_friends(pete)
            raise tornado.gen.Return(result)

        IOLoop.instance().run_sync(seed_db)
        actual = IOLoop.instance().run_sync(test)
        expected = set([jane, bill])
        assert actual == expected

        # now test the cache by clearing the database and repeating the test
        self.clear_db()
        actual = IOLoop.instance().run_sync(test)
        assert actual == expected

    def test_read_native_user_ids_from_facebook_user_ids(self):

        # native and Facebook IDs for some friends
        bill = ObjectId()
        jane = ObjectId()
        pete = ObjectId()
        bill_fb = "a"
        jane_fb = "b"
        pete_fb = "c"

        # a Facebook friend who isn't a user
        john_fb = "d"

        @tornado.gen.coroutine
        def seed_db(): 
            yield motor.Op(sundowner.data.users._conn.insert, [
                {"_id": bill, "facebook_id": bill_fb},
                {"_id": jane, "facebook_id": jane_fb},
                {"_id": pete, "facebook_id": pete_fb},
                ])

        @tornado.gen.coroutine
        def test():
            fb_user_ids = [pete_fb, john_fb, bill_fb]
            result = yield sundowner.data.users.\
                read_native_user_ids_from_facebook_user_ids(fb_user_ids)
            raise tornado.gen.Return(result)

        IOLoop.instance().run_sync(seed_db)
        actual = IOLoop.instance().run_sync(test)
        expected = set([pete, bill])
        assert actual == expected

