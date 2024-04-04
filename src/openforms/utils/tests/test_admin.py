from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from log_outgoing_requests.models import OutgoingRequestsLog
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.logging.models import TimelineLogProxy


@disable_admin_mfa()
class OutgoingRequestLogAdminTests(WebTest):
    def test_viewing_outgoing_request_log_details_in_admin_creates_log(self):
        user = UserFactory.create(is_superuser=True, is_staff=True)
        outgoing_request_log = OutgoingRequestsLog.objects.create(
            url="https://example.com", timestamp=timezone.now()
        )

        self.app.get(
            reverse(
                "admin:log_outgoing_requests_outgoingrequestslog_change",
                kwargs={"object_id": outgoing_request_log.id},
            ),
            user=user,
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/outgoing_request_log_details_view_admin.txt"
            ).count(),
            1,
        )
