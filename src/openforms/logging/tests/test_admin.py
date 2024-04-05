import json
from datetime import datetime, timezone as dt_timezone

from django.contrib.auth.models import Permission
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.logging.tests.factories import TimelineLogProxyFactory
from openforms.prefill.registry import register
from openforms.submissions.tests.factories import SubmissionFactory

from ..admin import TimelineLogProxyResource


@disable_admin_mfa()
class AVGAuditLogListViewTests(WebTest):
    def test_view(self):
        url = reverse("admin:logging_avgtimelinelogproxy_changelist")

        user = StaffUserFactory.create()
        permission = Permission.objects.get(
            content_type__app_label="logging", codename="view_avgtimelinelogproxy"
        )
        user.user_permissions.add(permission)
        self.client.force_login(user)

        submission = SubmissionFactory.create()
        # create AVG log
        logevent.submission_details_view_admin(submission, user)

        # create generic log
        TimelineLogProxyFactory.create(content_object=submission, user=user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # one log
        self.assertEqual(response.context_data["cl"].result_count, 1)

    def test_superuser_cant_delete_logs_with_bulk_action(self):
        submission = SubmissionFactory.create(completed_on=timezone.now())
        user = SuperUserFactory.create()

        logevent.submission_details_view_admin(submission, user)

        url = reverse("admin:logging_timelinelogproxy_changelist")
        changelist = self.app.get(url, user=user)

        html_form = changelist.forms["changelist-form"]

        # It is not possible to select the "delete_selected" option
        options = {
            value for value, *_ in html_form.fields.get("action")[0].options if value
        }
        self.assertEqual(options, {"export_admin_action"})

    def test_superuser_cant_delete_individual_logs(self):
        submission = SubmissionFactory.create(completed_on=timezone.now())
        user = SuperUserFactory.create()

        logevent.submission_details_view_admin(submission, user)
        log = TimelineLogProxy.objects.get(object_id=submission.id)

        url = reverse(
            "admin:logging_timelinelogproxy_delete", kwargs={"object_id": log.id}
        )

        self.app.get(url, user=user, expect_errors=403)

    @tag("gh-2850")
    def test_deleted_submission_doesnt_crash_logs(self):
        url = reverse("admin:logging_avgtimelinelogproxy_changelist")

        user = StaffUserFactory.create(
            user_permissions=["logging.view_avgtimelinelogproxy"]
        )
        self.client.force_login(user)

        submission = SubmissionFactory.create()

        logevent.prefill_retrieve_success(
            submission, register["haalcentraal"], ["name"]
        )

        submission.delete()

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)


class TimelineLogExportsTest(TestCase):
    def test_bare_timelinelog_export(self):
        user = StaffUserFactory.create()
        bare_log = TimelineLogProxyFactory.create(user=user)
        bare_log.timestamp = datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
        bare_log.save()

        dataset = TimelineLogProxyResource().export()

        self.assertEqual(
            json.loads(dataset.json),
            [
                {
                    "message": bare_log.message().strip(),
                    "user": _("Staff user {user}").format(user=user),
                    "related_object": None,
                    "timestamp": "2024-01-01T00:00:00+00:00",
                    "event": None,
                }
            ],
        )

    def test_timelinelog_export(self):
        submission = SubmissionFactory.create()
        submission.created_on = datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
        submission.save()
        user = StaffUserFactory.create()
        log = TimelineLogProxyFactory.create(
            content_object=submission, user=user, extra_data={"log_event": "test_event"}
        )
        log.timestamp = datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
        log.save()

        dataset = TimelineLogProxyResource().export()

        self.assertEqual(
            json.loads(dataset.json),
            [
                {
                    "message": log.message().strip(),
                    "user": _("Staff user {user}").format(user=user),
                    "related_object": _("{pk} - started on {started}").format(
                        pk=submission.pk,
                        started=localize(
                            timezone.localtime(
                                datetime(2024, 1, 1, tzinfo=dt_timezone.utc)
                            )
                        ),
                    ),
                    "timestamp": "2024-01-01T00:00:00+00:00",
                    "event": "test_event",
                }
            ],
        )
