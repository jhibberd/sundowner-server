"""Single subscriber to published activity messages, responsible for writing
them to the database.
"""

import json
import zmq
from sundowner.analytics.activity.store import ActivityStore


# NOTE If a subscriber is processing the messages at a slower rate than the
# publisher is publishing them then instead of messages being dropped (which
# I'd expect) the messages are being queued up somewhere. I've tried using
# socket.set_hwm to limit this queuing but to no effect.

class ActivitySub(object):

    @classmethod
    def run(cls):
        """Synchronously handle published messages in infinite loop."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")
        socket.setsockopt(zmq.SUBSCRIBE, "")
        while True:
            msg = socket.recv()
            msg = json.loads(msg)
            cls._handle(msg)

    @classmethod
    def _handle(cls, msg):
        ActivityStore.put(msg)


if __name__ == "__main__":
    ActivitySub.run()

