import datetime
import motor
import pymongo
import sundowner.config
import tornado.gen
from sundowner.analytics.activity.pub import Verb


class Database(object):

    def __init__(self, conn):
        self._analytics =   conn[sundowner.config.cfg["db-name-analytics"]]
        self._primary =     conn[sundowner.config.cfg["db-name-primary"]]

    _BATCH_SIZE = 100
    @tornado.gen.coroutine
    def get_recent_activity(self):

        result = []
        cursor = self._analytics.activity.find()
        cursor.sort([("_id", pymongo.DESCENDING)]).limit(self._BATCH_SIZE)
        while (yield cursor.fetch_next):
            activity = cursor.next_object()

            # augment actor data
            activity["actor_data"] = yield self.get_user(activity["actor"])

            # augment subject data (if available)
            if activity["verb"] in [Verb.CREATE, Verb.LIKE, Verb.DISLIKE]:
                activity["subject_data"] = \
                    yield motor.Op(
                        self._primary.content.find_one,
                        {"_id": activity["subject"]["content_id"]}) 

            # format time
            time = self._fmt_timestamp(activity["created_time"])

            # format actor
            actor = {
                "name": activity["actor_data"]["facebook"]["name"], 
                "id":   activity["actor"],
                }

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

    @tornado.gen.coroutine
    def get_user(self, user_id):
        result = yield motor.Op(
            self._primary.users.find_one, {"_id": user_id})
        raise tornado.gen.Return(result)

    @staticmethod
    def _fmt_timestamp(ts):
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S %d %b")

