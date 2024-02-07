from django.contrib.auth.models import Permission
from django.test import tag
from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.logging.tests.factories import TimelineLogProxyFactory
from openforms.prefill.registry import register
from openforms.submissions.tests.factories import SubmissionFactory


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
        self.assertIsNone(html_form.fields.get("action"))

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
