from datetime import UTC, datetime

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from freezegun import freeze_time
from log_outgoing_requests.models import OutgoingRequestsLog
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.logging.models import TimelineLogProxy


@disable_admin_mfa()
class OutgoingRequestLogAdminTests(WebTest):
    def test_view_404(self):
        user = UserFactory.create(is_superuser=True, is_staff=True)

        self.app.get(
            reverse(
                "admin:log_outgoing_requests_outgoingrequestslog_change",
                kwargs={"object_id": 123456},
            ),
            user=user,
            status=404,
        )

    @freeze_time(datetime(2024, 1, 1, tzinfo=UTC))
    @override_settings(LANGUAGE_CODE="en")
    def test_viewing_outgoing_request_log_details_in_admin_creates_log(self):
        user = UserFactory.create(is_superuser=True, is_staff=True)
        outgoing_request_log = OutgoingRequestsLog.objects.create(
            url="https://example.com", timestamp=timezone.now(), method="GET"
        )

        self.app.get(
            reverse(
                "admin:log_outgoing_requests_outgoingrequestslog_change",
                kwargs={"object_id": outgoing_request_log.pk},
            ),
            user=user,
        )

        log = TimelineLogProxy.objects.get(
            template="logging/events/outgoing_request_log_details_view_admin.txt"
        )
        self.assertEqual(
            log.message().strip(),
            "[2024-01-01 01:00:00 CET] (Outgoing request log "
            f"{outgoing_request_log.pk}): User Staff user {user} viewed outgoing "
            "request log GET https://example.com in the admin",
        )
