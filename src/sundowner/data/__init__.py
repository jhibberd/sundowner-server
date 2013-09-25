"""Establish a single connection to MongoDB using Motor, a non-blocking driver
for python Tornado applications, written by 10gen.

https://github.com/mongodb/motor

NOTE: currently requires the bleeding-edge version from GitHub as pip package
is missing critical features
"""

import motor
import sundowner.config
import sundowner.data.content
import sundowner.data.users
import sundowner.data.votes


def connect(host='localhost', port=27017):
    database = sundowner.config.cfg['database']
    client = motor.MotorClient(host, port).open_sync()
    db = client[database]
    sundowner.data.content.Data.init(db)
    sundowner.data.users.Data.init(db)
    sundowner.data.votes.Data.init(db)

