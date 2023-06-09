from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time
from log_outgoing_requests.models import OutgoingRequestsLog

from ..tasks import cleanup_request_logs


class TestLogTask(TestCase):
    @override_settings(LOG_OUTGOING_REQUESTS_MAX_AGE=1)  # delete if >= one hour old
    def test_cleanup_request_logs(self):
        """Assert that logs are cleaned if and only if created before specified time"""
        with freeze_time("2023-06-08T22:00:00Z") as frozen_time:
            OutgoingRequestsLog.objects.create(timestamp=timezone.now())
            frozen_time.move_to("2023-06-08T23:15:00Z")
            to_keep = OutgoingRequestsLog.objects.create(timestamp=timezone.now())

            cleanup_request_logs()

        self.assertQuerysetEqual(
            OutgoingRequestsLog.objects.all(),
            [to_keep.pk],
            transform=lambda record: record.pk,
        )
