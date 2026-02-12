import json

from django.contrib.auth.models import Permission
from django.template.response import TemplateResponse
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.logging import audit_logger
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
        audit_logger.info(
            "submission_details_view_admin",
            submission_uuid=str(submission.uuid),
            user=user.username,
        )

        # create generic log
        TimelineLogProxyFactory.create(content_object=submission, user=user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        assert isinstance(response, TemplateResponse)
        # one log
        assert response.context_data is not None
        self.assertEqual(response.context_data["cl"].result_count, 1)

    def test_superuser_cant_delete_logs_with_bulk_action(self):
        submission = SubmissionFactory.create(completed_on=timezone.now())
        user = SuperUserFactory.create()

        audit_logger.info(
            "submission_details_view_admin",
            submission_uuid=str(submission.uuid),
            user=user.username,
        )

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

        audit_logger.info(
            "submission_details_view_admin",
            submission_uuid=str(submission.uuid),
            user=user.username,
        )
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
        audit_logger.info(
            "prefill_retrieve_success",
            submission_uuid=str(submission.uuid),
            plugin=register["haalcentraal"],
            attributes=["name"],
        )
        submission.delete()

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)


class TimelineLogExportsTest(TestCase):
    def test_bare_timelinelog_export(self):
        user = StaffUserFactory.create()
        TimelineLogProxyFactory.create(user=user)

        dataset = TimelineLogProxyResource().export()

        # Asserting on `dataset.json` as it is the most straightforward
        json_data = json.loads(dataset.json)

        self.assertEqual(len(json_data), 1)
        for member in ["user", "related_object", "message", "event", "timestamp"]:
            self.assertIn(member, dataset.headers)

        self.assertIsNone(json_data[0]["related_object"])
        self.assertIsNone(json_data[0]["event"])

    def test_timelinelog_export(self):
        submission = SubmissionFactory.create()
        user = StaffUserFactory.create()
        TimelineLogProxyFactory.create(
            content_object=submission, user=user, extra_data={"log_event": "test_event"}
        )

        dataset = TimelineLogProxyResource().export()

        # Asserting on `dataset.json` as it is the most straightforward
        self.assertEqual(len(json.loads(dataset.json)), 1)
        for member in ["user", "related_object", "message", "event", "timestamp"]:
            self.assertIn(member, dataset.headers)
