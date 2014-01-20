import datetime
import motor
import os.path
import sundowner.config
import sys
import tornado.auth
import tornado.gen
import tornado.ioloop
import tornado.web
from bson import json_util
from bson.objectid import ObjectId
from sundowner_analytics.db import Database


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        user_json = self.get_secure_cookie("session")
        if not user_json: 
            return None
        return tornado.escape.json_decode(user_json)


class AuthLoginHandler(BaseHandler, tornado.auth.FacebookGraphMixin):
    # authentication logic based on:
    # https://github.com/facebook/tornado/blob/master/demos/facebook/facebook.py

    @tornado.web.asynchronous
    def get(self):

        redirect_uri = "%s://%s/auth/login?next=%s" % (
            self.request.protocol,
            self.request.host,
            tornado.escape.url_escape(self.get_argument("next", "/")))
        fb_app_id =         sundowner.config.cfg["analytics"]["fb-app-id"]
        fb_app_secret =     sundowner.config.cfg["analytics"]["fb-app-secret"]

        if self.get_argument("code", False):
            self.get_authenticated_user(
                redirect_uri=   redirect_uri,
                client_id=      fb_app_id,
                client_secret=  fb_app_secret,
                code=           self.get_argument("code"),
                callback=       self._on_auth)
            return
        self.authorize_redirect(
            redirect_uri=   redirect_uri,
            client_id=      fb_app_id)

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Facebook auth failed")
        self.set_secure_cookie("session", tornado.escape.json_encode(user))
        self.redirect(self.get_argument("next", "/"))


class ActivityHandler(BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        db_conn = self.settings["db_conn"]
        activity = yield Database(db_conn).get_recent_activity()
        self.render("activity.html", activity=activity)


class UsersHandler(BaseHandler):

    @tornado.web.authenticated
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
        (r"/auth/login",                AuthLoginHandler),
        ],
        cookie_secret=  "ytLrgLgbRxuMnsi9Oz9kmXUV3+ycoUSUnDGTfIBIddA=",
        xsrf_cookies=   True,
        login_url=      "/auth/login",
        template_path=  os.path.join(os.path.dirname(__file__), "templates"),
        db_conn=        db_conn,
        debug=          True)
    application.listen(sundowner.config.cfg["analytics"]["port"])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

