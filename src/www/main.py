import os.path
import tornado.ioloop
import tornado.web


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
    application = tornado.web.Application([
        (r"/terms/",        TermsHandler),
        (r"/privacy/",      PrivacyHandler),
        (r"/support/",      SupportHandler),
        ], 
        template_path=os.path.join(os.path.dirname(__file__), "templates"))
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

