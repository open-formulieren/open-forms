from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.logging import logevent
from openforms.logging.tests.factories import TimelineLogProxyFactory
from openforms.submissions.tests.factories import SubmissionFactory


class AVGAuditLogListViewTests(TestCase):
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
