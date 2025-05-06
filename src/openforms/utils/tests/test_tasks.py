from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings
from django.utils import timezone

from ..tasks import run_management_command


class RunManagementCommandTaskTests(TestCase):
    @override_settings(SESSION_ENGINE="django.contrib.sessions.backends.db")
    def test_clearsessions(self):
        # create an expired session
        Session.objects.create(session_key="dummy", expire_date=timezone.now())

        run_management_command(command="clearsessions")

        self.assertFalse(Session.objects.exists())
