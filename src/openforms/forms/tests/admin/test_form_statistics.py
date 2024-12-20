from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from django_webtest import WebTest
from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.logging import logevent
from openforms.registrations.contrib.demo.plugin import DemoRegistration
from openforms.submissions.tests.factories import SubmissionFactory

from ...forms import ExportStatisticsForm


@disable_admin_mfa()
class FormStatisticsExportAdminTests(WebTest):

    admin_url = reverse_lazy("admin:formstatistics_export")

    def test_access_control_no_access(self):
        # various flavours of users do not have access, only if the right permissions
        # are set are you allowed in
        invalid_users = (
            (
                "plain user",
                UserFactory.create(),
                302,
            ),
            (
                "staff user without perms",
                UserFactory.create(is_staff=True),
                403,
            ),
            (
                "user with perms no staff",
                UserFactory.create(
                    is_staff=False, user_permissions=["forms.view_formstatistics"]
                ),
                302,
            ),
        )

        for label, user, expected_status in invalid_users:
            with self.subTest(label, expected_status=expected_status):
                response = self.app.get(
                    self.admin_url,
                    user=user,
                    auto_follow=False,
                    status=expected_status,
                )

                self.assertEqual(response.status_code, expected_status)

    def test_navigate_from_changelist(self):
        user = UserFactory.create(
            is_staff=True, user_permissions=["forms.view_formstatistics"]
        )
        changelist = self.app.get(
            reverse("admin:forms_formstatistics_changelist"), user=user
        )

        export_page = changelist.click(_("Export submission statistics"))

        self.assertEqual(export_page.request.path, self.admin_url)

    def test_successful_export_downloads_file(self):
        user = UserFactory.create(
            is_staff=True,
            user_permissions=["forms.view_formstatistics"],
        )
        # create some log records for submissions
        with freeze_time("2024-12-20T16:44:00+01:00"):
            sub1, sub2, sub3 = SubmissionFactory.create_batch(
                3, registration_success=True
            )
            plugin = DemoRegistration("demo")
            logevent.registration_success(sub1, plugin=plugin)
            logevent.registration_success(sub2, plugin=plugin)
            logevent.registration_success(sub3, plugin=plugin)

        export_page = self.app.get(self.admin_url, user=user)
        form = export_page.forms["export-statistics"]

        # fill out the form and submit it
        form["start_date"] = "2024-12-01"
        form["end_date"] = "2025-01-01"
        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(int(response["Content-Length"]), 0)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="submissions_2024-12-01_2025-01-01.xlsx"',
        )
