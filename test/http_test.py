"""Make some basic HTTP requests to the API to ensure basic functionality is
working.
"""

import json
import pymongo
import requests
from bson.objectid import ObjectId
from pprint import pprint


host = 'http://localhost:8050'
user_id = ObjectId()

db = pymongo.MongoClient()['sundowner_sandbox']
db.users.remove()
db.users.insert({'_id': user_id, 'username': 'James'}, safe=True)
db.content.remove()
db.votes.remove()

print 'Posting content'
data = json.dumps({
    'lng':          1,
    'lat':          1,
    'text':         'Hello world',
    'user_id':      str(user_id),
    'accuracy':     5,
    'url':          'http://www.foo.com',
    })
r = requests.post(host + '/content', data=data)
pprint(r.json())
print

print 'Getting content'
data = {
    'lng':          1,
    'lat':          1,
    'user_id':      str(user_id),
    }
r = requests.get(host + '/content', params=data)
pprint(r.json())
content_id = r.json()['data'][0]['id']
print

print 'Voting up content'
data = json.dumps({
    'content_id':   content_id,
    'user_id':      str(user_id),
    'vote':         1,
    })
r = requests.post(host + '/votes', data=data)
pprint(r.json())
print

print 'Voting up same content again'
data = json.dumps({
    'content_id':   content_id,
    'user_id':      str(user_id),
    'vote':         1,
    })
r = requests.post(host + '/votes', data=data)
pprint(r.json())
print

