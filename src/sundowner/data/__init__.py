"""Create a single thread-safe connection to mongoDB and use it to initialise
the classes that provide access to the collections.

Thread-safety:
http://api.mongodb.org/python/current/faq.html#is-pymongo-thread-safe
"""

import pymongo
import sundowner.config
import sundowner.data.content
import sundowner.data.users
import sundowner.data.votes
from sundowner.config import cfg


def connect(host='localhost', port=27017):
    database = sundowner.config.cfg['database']
    conn = pymongo.MongoClient(host, port)[database]
    sundowner.data.content.Data.init(conn)
    sundowner.data.users.Data.init(conn)
    sundowner.data.votes.Data.init(conn)

