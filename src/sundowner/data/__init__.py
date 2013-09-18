"""Create a single thread-safe connection to mongoDB and use it to initialise
the classes that provide access to the collections.

Thread-safety:
http://api.mongodb.org/python/current/faq.html#is-pymongo-thread-safe
"""

import pymongo
import sundowner.data.content
import sundowner.data.users
import sundowner.data.votes


def connect(host='localhost', port=27017):
    conn = pymongo.MongoClient(host, port).sundowner_instagram
    sundowner.data.content.Data.init(conn)
    sundowner.data.users.Data.init(conn)
    sundowner.data.votes.Data.init(conn)

