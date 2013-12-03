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


def main():

    try:
        config_filepath = sys.argv[1]
    except IndexError:
        raise Exception("No config file specified")
    sundowner.config.init(config_filepath)

    application = tornado.web.Application([
        (r"/",              MainHandler),
        (r"/terms/",        TermsHandler),
        (r"/privacy/",      PrivacyHandler),
        (r"/support/",      SupportHandler),
        ], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=True)
    application.listen(sundowner.config.cfg["www-port"])
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

