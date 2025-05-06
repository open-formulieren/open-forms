from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

from ..utils import append_to_session_list


class SessionUpdateTests(TestCase):
    def test_just_in_time_refresh(self):
        session = SessionStore()
        session["some-list"] = ["initial"]
        session.save()
        session_key = session.session_key

        def _race():
            session = SessionStore(session_key)
            session["some-list"] = ["initial", "second"]
            session.save()  # close_db_connections()

        # other key gets modified and runs in its own thread, but crucially *after*
        # we instantiated and loaded our own session
        _race()

        append_to_session_list(session, "some-list", "third")

        session.load()
        self.assertEqual(session["some-list"], ["initial", "second", "third"])
