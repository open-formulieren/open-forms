from datetime import UTC, datetime
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cookie_consent.models import LogItem
from django_webtest import WebTest
from freezegun import freeze_time
from log_outgoing_requests.models import OutgoingRequestsLog
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.logging.models import TimelineLogProxy

from ..admin import replace_cookie_log_admin


@disable_admin_mfa()
class OutgoingRequestLogAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        # prevent celery tasks from being scheduled
        patcher = patch("log_outgoing_requests.models.schedule_config_reset")
        patcher.start()
        self.addCleanup(patcher.stop)

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


@disable_admin_mfa()
class CookieLogAdminTests(TestCase):
    @override_settings(COOKIE_CONSENT_LOG_ENABLED=True)
    def test_admin_is_readonly_when_cookie_log_is_enabled(self):
        # initial setup, skipped because by default log is disabled
        admin.site.register(LogItem)
        self.addCleanup(lambda: admin.site.unregister(LogItem))
        replace_cookie_log_admin()

        model_admin = admin.site.get_model_admin(LogItem)

        request = RequestFactory().get("/admin/cookie_consent/logitem/")
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
