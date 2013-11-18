import datetime
import motor
import os.path
import sundowner.config
import sys
import tornado.gen
import tornado.ioloop
import tornado.web
from bson import json_util
from bson.objectid import ObjectId
from sundowner_analytics.db import Database


class ActivityHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        db_conn = self.settings["db_conn"]
        activity = yield Database(db_conn).get_recent_activity()
        self.render("activity.html", activity=activity)


class UsersHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, user_id):
        user_id = ObjectId(user_id)
        db_conn = self.settings["db_conn"]
        user = yield Database(db_conn).get_user(user_id)
        self.render("user.html", user=json_util.dumps(user))


def main():

    # init config
    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception('No config file specified')
    sundowner.config.init(config_filepath)

    db_conn = motor.MotorClient(
        sundowner.config.cfg["db-host"],
        sundowner.config.cfg["db-port"],
        ).open_sync()
    application = tornado.web.Application([
        (r"/",                          ActivityHandler),
        (r"/users/([0-9a-f]{24})/?",    UsersHandler),
        ], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        db_conn=db_conn,
        debug=True)
    application.listen(sundowner.config.cfg["analytics-port"])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

