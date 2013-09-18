import json
import sundowner.data
import sundowner.data.content
import sundowner.data.users
import sundowner.data.votes
import sundowner.ranking
import time
import tornado.ioloop
import tornado.web
from operator import itemgetter
from sundowner.data.votes import Vote


def _trimdict(d):
    """Remove all entries with a None value."""
    return dict([(k, v) for k,v in d.items() if v is not None])

def _get_target_vector(lng, lat):
    """Return the vector used as a target when scoring the proximity of 
    content.

    Vote values are set to 0 
    Vote values are set as 0 because the delta function for calculating the
    vote distance always compares the content's vote score against 1 (the best
    vote score).
    """
    now = long(time.time())
    return (
        lng,    # longitude 
        lat,    # latitude
        now,    # created time
        0,      # votes up
        0,      # votes down
        )

class _ContentHandler(tornado.web.RequestHandler):

    def get(self):
        """Return top content near a location."""

        lng =       float(self.get_argument('longitude'))
        lat =       float(self.get_argument('latitude'))
        user_id =   self.get_argument('user_id')

        # get all nearby content
        target_vector = _get_target_vector(lng, lat)
        content = sundowner.data.content.Data.get_nearby(lng, lat)

        # filter content that the user has voted down
        user_votes = sundowner.data.votes.Data.get_user_votes(user_id)
        rule = lambda content: (content['_id'], Vote.DOWN) not in user_votes
        content = filter(rule, content)

        # rank content and return top
        top_content = sundowner.ranking.top(content, target_vector, n=10)

        # replace user IDs with usernames
        user_ids = map(itemgetter('user_id'), top_content)
        username_map = sundowner.data.users.Data.get_usernames(user_ids)

        result = []
        for content in top_content:
            username = username_map[content['user_id']]
            result.append(_trimdict({
                'id':           str(content['_id']),
                'title':        content['title'],
                'url':          content.get('url'),
                'username':     username,
                }))

        self.write({'data': result})

    def post(self):
        """Save content to the database."""
        
        payload =       json.loads(self.request.body)
        longitude =     payload['longitude']
        latitude =      payload['latitude']
        title =         payload['title']
        user_id =       payload['user_id']
        accuracy =      payload['accuracy']
        url =           payload.get('url')

        # TODO validate user ID

        created =       long(time.time())
        doc = _trimdict({
            'title':            title,
            'url':              url,
            'created':          created,
            'user_id':          user_id,
            'accuracy':         accuracy, # meters
            'loc': {
                'type':         'Point',
                'coordinates':  [longitude, latitude],
                }
            })
        sundowner.data.content.Data.put(doc)


class _VotesHandler(tornado.web.RequestHandler):

    def post(self):
        """Register a vote up or down against a piece of content."""

        payload =       json.loads(self.request.body)
        content_id =    payload['content_id']
        user_id =       payload['user_id']
        vote =          payload['vote']

        # TODO validate all 3 fields
        # https://blog.serverdensity.com/checking-if-a-document-exists-mongodb-slow-findone-vs-find/

        success = sundowner.data.votes.Data.put(content_id, user_id, vote)
        if success:
            sundowner.data.content.Data.inc_vote(content_id, vote)
        else:
            # the vote has already been placed; silently fail
            pass


application = tornado.web.Application([
    (r'/content',   _ContentHandler),   # GET, POST
    (r'/votes',     _VotesHandler),     # POST
    ])

def main():
    sundowner.data.connect()
    application.listen(8050)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

