"""Superclass for test cases."""

import motor
import random
import sundowner.config
import sundowner.data
import tornado.gen
import unittest
from sundowner.cache import _ThreadSafeCacheConnection
from tornado.ioloop import IOLoop


class TestBase(unittest.TestCase):

    _CFG_PATH = "/home/jhibberd/projects/sundowner/cfg/dev.yaml"
    def setUp(self):
        """Prepare the environment for testing."""
        sundowner.config.init(self._CFG_PATH)
        sundowner.data.connect()
        self.clear_db()
        _ThreadSafeCacheConnection.get().flushall()

    @classmethod
    def clear_db(cls):
        """Clear all collections in the database."""
        @tornado.gen.coroutine
        def f():
            yield motor.Op(sundowner.data.users._conn.remove, None)
            yield motor.Op(sundowner.data.content._conn.remove, None)
        IOLoop.instance().run_sync(f)

    _NOUNS = map(lambda ln: ln[:-2], open("nouns.txt").readlines())
    @classmethod
    def rand_noun(cls):
        """Return a random english noun string."""
        return random.choice(cls._NOUNS)

