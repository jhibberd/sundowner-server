import os.path
import sundowner.config
import sys
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class TermsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("terms.html")


class PrivacyHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("privacy.html")


class SupportHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("support.html")


class JobsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("jobs.html")


def main():

    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception("No config file specified")
    sundowner.config.init(config_filepath)

    static_path = os.path.join(os.path.dirname(__file__), "static")
    favicon_path = os.path.join(static_path, "favicon.ico")
    application = tornado.web.Application([
        (r"/favicon.ico",   tornado.web.StaticFileHandler, {"path": favicon_path}), 
        (r"/",              MainHandler),
        (r"/terms/?",       TermsHandler),
        (r"/privacy/?",     PrivacyHandler),
        (r"/support/?",     SupportHandler),
        (r"/jobs/?",        JobsHandler),
        ], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=static_path,
        debug=True)
    application.listen(sundowner.config.cfg["www-port"])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

