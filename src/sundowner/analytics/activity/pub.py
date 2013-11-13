"""Publish system activity messages to a 0MQ socket (returning immediately)."""

import time
import zmq
from bson import json_util


class ActivityPub(object):

    # Convenience Methods ------------------------------------------------------

    def write_user_create_content(self, user_id, content_id):
        self._write_activity(user_id, Verb.CREATE, {
            "content_id": content_id,
            })

    def write_user_view_content(self, user_id, lng, lat):
        self._write_activity(user_id, Verb.VIEW, {
            "lng": lng,
            "lat": lat,
            })

    def write_user_like_content(self, user_id, content_id):
        self._write_activity(user_id, Verb.LIKE, {
            "content_id": content_id,
            })

    def write_user_dislike_content(self, user_id, content_id):
        self._write_activity(user_id, Verb.DISLIKE, {
            "content_id": content_id,
            })

    # --------------------------------------------------------------------------

    # TODO do we not need to use the 0MQ tornado loop here?
    def _get_conn(self):
        """Return on-demand connection to 0MQ socket."""
        if not hasattr(self, "_conn"):
            context = zmq.Context()
            socket = context.socket(zmq.PUB)
            socket.bind("tcp://*:5556")
            self._conn = socket
        return self._conn

    def _write_activity(self, actor, verb, subject):
        """Create activity doc, serialize and send to 0MQ socket."""

        try:
            doc = {
                "created_time":     long(time.time()),
                "actor":            actor,
                "verb":             verb,
                "subject":          subject,
                }
            self._get_conn().send(json_util.dumps(doc))

        except Exception as e:
            # this is an auxilliary feature and shouldn't cause a request to
            # fail, so just write the error to stdout for now
            print e


class Verb(object):
    CREATE =    "created"
    VIEW =      "view"
    LIKE =      "like"
    DISLIKE =   "dislike"

