import json
import sundowner.database
import sundowner.ranking
import time
import tornado.ioloop
import tornado.web


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

class _Handler(tornado.web.RequestHandler):

    def get(self):
        """Return top content near a location."""

        lng = float(self.get_argument('longitude'))
        lat = float(self.get_argument('latitude'))

        target_vector = _get_target_vector(lng, lat)
        content = sundowner.database.Database.get_content_nearby(lng, lat)
        top_content = sundowner.ranking.top(content, target_vector, n=10)

        # TODO cleanup once Android and iOS apps have been updated
        result = []
        for doc in top_content:
            result.append(_trimdict({
                'title':        doc['title'],
                'url':          doc.get('url'),
                'created':      doc['created'],
                'username':     doc['username'],
                'distance':     0,
                }))

        self.write({'data': result})

    def post(self):
        """Save content to the database."""
        
        payload =       json.loads(self.request.body)
        longitude =     payload['longitude']
        latitude =      payload['latitude']
        title =         payload['title']
        username =      payload['username']
        accuracy =      payload['accuracy']
        url =           payload.get('url')

        created =       long(time.time())
        doc = _trimdict({
            'title':            title,
            'url':              url,
            'created':          created,
            'username':         username,
            'accuracy':         accuracy, # meters
            'loc': {
                'type':         'Point',
                'coordinates':  [longitude, latitude],
                }
            })
        sundowner.database.Database.put(doc)


application = tornado.web.Application([
    (r'/', _Handler),
])

def main():
    sundowner.database.Database.connect()
    application.listen(8050)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

