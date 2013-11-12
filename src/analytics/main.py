import datetime
import motor
import os.path
import tornado.gen
import tornado.ioloop
import tornado.web
from sundowner.analytics.activity.pub import Verb


class ActivityStore(object):

    _BATCH_SIZE = 10

    @tornado.gen.coroutine
    @classmethod
    def get(cls, db_conn):

        db_analytics =  db_conn["sundowner_analytics"]
        db_primary =    db_conn["sundowner_sandbox"]

        cursor = db_analytics.actvity.find(spec).limit(cls._BATCH_SIZE)
        while (yield cursor.fetch_next):
            activity = cursor.next_object()

            # augment actor data
            activity["actor_data"] = \
                yield db_primary.users.find_one(
                    {"_id": activity["actor"]}) 

            # augment subject data (if available)
            if activity["verb"] in [verb.CREATE, verb.LIKE, verb.DISLIKE]:
                activity["subject_data"] = \
                    yield db_primary.conf.find_one(
                        {"_id": activity["subject"]["content_id"]}) 

            # format time
            time = cls._fmt_timestamp(activity["created_time"])

            # format actor
            actor = "%s (%s)" % \
                (activity["actor_data"]["facebook"]["name"], activity["actor"])

            # format verb
            verb = activity["verb"] 

            # format subject
            if activity["verb"] in [verb.CREATE, verb.LIKE, verb.DISLIKE]:
                subject = "\"%s\" by %s (%s)" % (
                    activity["subject_data"]["text"],
                    activity["actor_data"]["facebook"]["name"],
                    activity["actor"])
            else:
                subject = "%s, %s" % (subject["lng"], subject["lat"])

            yield {
                "time":     time,
                "actor":    actor,
                "verb":     verb,
                "subject":  subject,
                }

    @staticmethod
    def _fmt_timestamp(ts):
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S %d %b")


class Handler(tornado.web.RequestHandler):
    def get(self):
        db_conn = self.setting["db_conn"]
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

