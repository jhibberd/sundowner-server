"""Abstraction of the database used for storing system activity."""

from pymongo import MongoClient
import sundowner.config


class ActivityStore(object):

    @classmethod
    def put(cls, doc):
        """Write the activity doc "doc" to the collection."""
        cls._get_conn().insert(doc)
        
    @classmethod
    def _get_conn(cls):
        """Return on-demand connection the the MongoDB collection."""
        if not hasattr(cls, "_conn"):
            client = MongoClient(
                sundowner.config.cfg["db-host"],
                sundowner.config.cfg["db-port"],
                )
            db_name = sundowner.config.cfg["db-name-analytics"]
            cls._conn = client[db_name].activity
        return cls._conn

