"""Errors generated by the platform."""

import httplib
import tornado.web


class BadRequestError(tornado.web.HTTPError):

    def __init__(self, message):
        super(BadRequestError, self).__init__(httplib.BAD_REQUEST)
        self.message = message

