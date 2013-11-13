import datetime
import motor
import os.path
import pymongo
import tornado.gen
import tornado.ioloop
import tornado.web
from sundowner.analytics.activity.pub import Verb


class ActivityStore(object):

    _BATCH_SIZE = 10

    @classmethod
    @tornado.gen.coroutine
    def get(cls, db_conn):

        db_analytics =  db_conn["sundowner_analytics"]
        db_primary =    db_conn["sundowner_sandbox"]

        result = []
        cursor = db_analytics.activity.find()
        cursor.sort([("_id", pymongo.DESCENDING)]).limit(cls._BATCH_SIZE)
        while (yield cursor.fetch_next):
            activity = cursor.next_object()

            # augment actor data
            activity["actor_data"] = \
                yield db_primary.users.find_one(
                    {"_id": activity["actor"]}) 

            # augment subject data (if available)
            if activity["verb"] in [Verb.CREATE, Verb.LIKE, Verb.DISLIKE]:
                activity["subject_data"] = \
                    yield db_primary.content.find_one(
                        {"_id": activity["subject"]["content_id"]}) 

            # format time
            time = cls._fmt_timestamp(activity["created_time"])

            # format actor
            actor = "%s (%s)" % \
                (activity["actor_data"]["facebook"]["name"], activity["actor"])

            # format verb
            verb = activity["verb"] 

            # format subject
            if activity["verb"] in [Verb.CREATE, Verb.LIKE, Verb.DISLIKE]:
                subject = "\"%s\" by %s (%s)" % (
                    activity["subject_data"]["text"],
                    activity["actor_data"]["facebook"]["name"],
                    activity["actor"])
            else:
                subject = "%s, %s" % (
                    activity["subject"]["lng"], 
                    activity["subject"]["lat"])

            # format location
            if activity["verb"] == Verb.VIEW:
                location = {
                    "lat":  activity["subject"]["lat"],
                    "lng":  activity["subject"]["lng"],
                    }
            else:
                location = None

            result.append({
                "time":     time,
                "actor":    actor,
                "verb":     verb,
                "subject":  subject,
                "location": location,
                })

        raise tornado.gen.Return(result)

    @staticmethod
    def _fmt_timestamp(ts):
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S %d %b")


class Handler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        db_conn = self.settings["db_conn"]
        activity = yield ActivityStore.get(db_conn)
        self.render("activity.html", activity=activity)


def main():
    db_conn = motor.MotorClient().open_sync()
    application = tornado.web.Application([
        (r"/", Handler),
        ], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        db_conn=db_conn,
        debug=True)
    application.listen(82)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

