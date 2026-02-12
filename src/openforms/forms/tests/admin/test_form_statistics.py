from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from django_webtest import WebTest
from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.logging import audit_logger
from openforms.logging.constants import (
    FORM_SUBMIT_SUCCESS_EVENT,
    REGISTRATION_SUCCESS_EVENT,
)
from openforms.registrations.contrib.demo.plugin import DemoRegistration
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ...forms import ExportStatisticsForm
from ..factories import FormFactory


def _log_form_submit_success(submission: Submission) -> None:
    """
    Lightweight helper to log the form submit event.

    Keep in sync with :meth:`openforms.submissions.api.mixins.SubmissionCompletionMixin._complete_submission`.
    """
    audit_logger.info(FORM_SUBMIT_SUCCESS_EVENT, submission_uuid=str(submission.uuid))


@disable_admin_mfa()
class SubmissionStatisticsAdminTests(WebTest):
    admin_url = reverse_lazy("admin:forms_formsubmissionstatistics_changelist")

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
                    is_staff=False,
                    user_permissions=["forms.view_formsubmissionstatistics"],
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

    def test_list_correct_statistics(self):
        superuser = SuperUserFactory.create()
        # Create different amounts of submissions for two different forms
        form_1 = FormFactory.create(name="Order coffee")
        form_2 = FormFactory.create(name="Request bathroom break")
        submission1 = SubmissionFactory.create(completed=True, form=form_1)
        _log_form_submit_success(submission1)
        submission2 = SubmissionFactory.create(completed=True, form=form_1)
        _log_form_submit_success(submission2)
        submission3 = SubmissionFactory.create(completed=True, form=form_2)
        _log_form_submit_success(submission3)

        changelist_page = self.app.get(self.admin_url, user=superuser)

        rows = changelist_page.pyquery("#result_list tbody tr")
        self.assertEqual(rows.length, 2)
        self.assertContains(changelist_page, "Order coffee", count=1)
        self.assertContains(changelist_page, "Request bathroom break", count=1)

        # check the reported counts
        form_1_row, form_2_row = rows.eq(0), rows.eq(1)
        self.assertEqual(form_1_row.find(".field-submission_count").text(), "2")
        self.assertEqual(form_2_row.find(".field-submission_count").text(), "1")

    def test_search_by_form_name(self):
        superuser = SuperUserFactory.create()
        # Create different amounts of submissions for two different forms
        form_1 = FormFactory.create(name="Order coffee")
        form_2 = FormFactory.create(name="Request bathroom break")
        submission1 = SubmissionFactory.create(completed=True, form=form_1)
        _log_form_submit_success(submission1)
        submission2 = SubmissionFactory.create(completed=True, form=form_1)
        _log_form_submit_success(submission2)
        submission3 = SubmissionFactory.create(completed=True, form=form_2)
        _log_form_submit_success(submission3)

        _changelist_page = self.app.get(self.admin_url, user=superuser)
        search_form = _changelist_page.forms["changelist-search"]
        search_form["q"] = "Coffee"
        changelist_page = search_form.submit()

        rows = changelist_page.pyquery("#result_list tbody tr")
        self.assertEqual(rows.length, 1)
        self.assertContains(changelist_page, "Order coffee", count=1)

        # check the reported counts
        count = rows.eq(0).find(".field-submission_count").text()
        self.assertEqual(count, "2")

    def test_date_range_filter(self):
        superuser = SuperUserFactory.create()
        form = FormFactory.create(name="Order coffee")
        # create submissions at different points in time
        with freeze_time("2024-10-07T12:00:00Z"):
            submission1 = SubmissionFactory.create(completed=True, form=form)
            _log_form_submit_success(submission1)
        with freeze_time("2025-01-03T10:00:00Z"):
            submission1 = SubmissionFactory.create(completed=True, form=form)
            _log_form_submit_success(submission1)
        with freeze_time("2025-01-04T23:59:59+01:00"):
            submission1 = SubmissionFactory.create(completed=True, form=form)
            _log_form_submit_success(submission1)

        _changelist_page = self.app.get(self.admin_url, user=superuser)
        # this library translates the form ID from the label, wtf
        form_id = f"{_('submitted between').replace(' ', '-')}-form"
        filter_form = _changelist_page.forms[form_id]

        with self.subTest("filter 2024 submissions"):
            filter_form["timestamp__range__gte"] = "2024-01-01"
            filter_form["timestamp__range__lte"] = "2024-12-31"

            changelist_page = filter_form.submit()

            rows = changelist_page.pyquery("#result_list tbody tr")
            self.assertEqual(rows.length, 1)
            count = rows.eq(0).find(".field-submission_count").text()
            self.assertEqual(count, "1")

        with self.subTest("filter 2025 submissions"):
            filter_form["timestamp__range__gte"] = "2025-01-01"
            filter_form["timestamp__range__lte"] = "2025-01-04"

            changelist_page = filter_form.submit()

            rows = changelist_page.pyquery("#result_list tbody tr")
            self.assertEqual(rows.length, 1)
            count = rows.eq(0).find(".field-submission_count").text()
            self.assertEqual(count, "2")


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
                    is_staff=False,
                    user_permissions=["forms.view_formsubmissionstatistics"],
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
            is_staff=True, user_permissions=["forms.view_formsubmissionstatistics"]
        )
        changelist = self.app.get(
            reverse("admin:forms_formsubmissionstatistics_changelist"), user=user
        )

        export_page = changelist.click(_("Export submission statistics"))

        self.assertEqual(export_page.request.path, self.admin_url)

    def test_successful_export_downloads_file(self):
        user = UserFactory.create(
            is_staff=True,
            user_permissions=["forms.view_formsubmissionstatistics"],
        )
        plugin = DemoRegistration("demo")
        audit_log = audit_logger.bind(plugin=plugin)
        # create some log records for submissions
        with freeze_time("2024-12-20T16:44:00+01:00"):
            sub1, sub2, sub3 = SubmissionFactory.create_batch(
                3, registration_success=True
            )
            audit_log.info("registration_success", submission_uuid=str(sub1.uuid))
            audit_log.info("registration_success", submission_uuid=str(sub2.uuid))
            audit_log.info("registration_success", submission_uuid=str(sub3.uuid))

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

    def test_export_form_filters(self):
        """
        Test that the form filters correctly filter down the matching log records.
        """
        plugin = DemoRegistration("demo")
        audit_log = audit_logger.bind(plugin=plugin)
        form1, form2, form3 = FormFactory.create_batch(3)
        with freeze_time("2024-12-20T16:44:00+01:00"):
            registered_submission_1 = SubmissionFactory.create(
                form=form1,
                registration_success=True,
                public_registration_reference="SUB-01",
            )
            audit_log.info(
                "registration_success",
                submission_uuid=str(registered_submission_1.uuid),
            )

            failed_submission = SubmissionFactory.create(
                form=form1,
                registration_failed=True,
                public_registration_reference="FAIL-01",
            )
            audit_log.warning(
                "registration_failure",
                submission_uuid=str(failed_submission.uuid),
                exc_info=Exception("nope"),
            )
        with freeze_time("2024-11-20T12:00:00+01:00"):
            registered_submission_2 = SubmissionFactory.create(
                form=form2,
                registration_success=True,
                public_registration_reference="SUB-02",
            )
            audit_log.info(
                "registration_success",
                submission_uuid=str(registered_submission_2.uuid),
            )

        with freeze_time("2024-12-05T12:00:00+01:00"):
            registered_submission_3 = SubmissionFactory.create(
                form=form3,
                registration_success=True,
                public_registration_reference="SUB-03",
            )
            audit_log.info(
                "registration_success",
                submission_uuid=str(registered_submission_3.uuid),
            )

        with freeze_time("2024-12-06T10:00:00+01:00"):
            registered_submission_4 = SubmissionFactory.create(
                form=form3,
                registration_success=True,
                public_registration_reference="SUB-04",
            )
            audit_log.info(
                "registration_success",
                submission_uuid=str(registered_submission_4.uuid),
            )

        with self.subTest("filter on start date"):
            export_form1 = ExportStatisticsForm(
                data={
                    "kind": REGISTRATION_SUCCESS_EVENT,
                    "start_date": "2024-12-14",
                    "end_date": "2024-12-31",
                }
            )
            export_form1_valid = export_form1.is_valid()
            assert export_form1_valid

            dataset1 = export_form1.export()

            self.assertEqual(len(dataset1), 1)
            self.assertEqual(dataset1[0][0], "SUB-01")

        with self.subTest("filter on end date"):
            export_form2 = ExportStatisticsForm(
                data={
                    "kind": REGISTRATION_SUCCESS_EVENT,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-05",
                }
            )
            export_form2_valid = export_form2.is_valid()
            assert export_form2_valid

            dataset2 = export_form2.export()

            self.assertEqual(len(dataset2), 2)
            self.assertEqual(dataset2[0][0], "SUB-02")
            self.assertEqual(dataset2[1][0], "SUB-03")

        with self.subTest("filter on subset of forms"):
            export_form3 = ExportStatisticsForm(
                data={
                    "kind": REGISTRATION_SUCCESS_EVENT,
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "limit_to_forms": [form2.pk, form3.pk],
                }
            )
            export_form3_valid = export_form3.is_valid()
            assert export_form3_valid

            dataset3 = export_form3.export()
            self.assertEqual(len(dataset3), 3)
            self.assertEqual(dataset3[0][0], "SUB-02")
            self.assertEqual(dataset3[1][0], "SUB-03")
            self.assertEqual(dataset3[2][0], "SUB-04")
