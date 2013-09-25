"""Establish a single connection to MongoDB using Motor, a non-blocking driver
for python Tornado applications, written by 10gen.

https://github.com/mongodb/motor

NOTE: currently requires the bleeding-edge version from GitHub as pip package
is missing critical features
"""

import motor
import sundowner.config
import tornado.ioloop
from sundowner.data import content as content_data
from sundowner.data import users as users_data
from sundowner.data import votes as votes_data


content =   None
users =     None
votes =     None

def connect(host='localhost', port=27017):
    global content, users, votes

    database = sundowner.config.cfg['database']
    client = motor.MotorClient(host, port).open_sync()
    db = client[database]

    content = content_data.Data(db)
    users = users_data.Data(db)
    votes = votes_data.Data(db)

    tornado.ioloop.IOLoop.current().run_sync(content.ensure_indexes)
    tornado.ioloop.IOLoop.current().run_sync(users.ensure_indexes)
    tornado.ioloop.IOLoop.current().run_sync(votes.ensure_indexes)
    
