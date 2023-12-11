from typing import cast
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from django_webtest import WebTest
from furl import furl
from rest_framework import status

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.forms.models import FormLogic, FormVariable
from openforms.forms.tests.factories import FormLogicFactory
from openforms.logging import logevent, logic
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.logic.rules import EvaluatedRule
from openforms.tests.utils import disable_2fa

from ...config.models import GlobalConfiguration
from ..constants import PostSubmissionEvents, RegistrationStatuses
from ..models import Submission
from .factories import SubmissionFactory, SubmissionValueVariableFactory


class TestSubmissionAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        cls.submission_1 = SubmissionFactory.from_components(
            [
                {"type": "textfield", "key": "adres"},
                {"type": "textfield", "key": "voornaam"},
                {"type": "textfield", "key": "familienaam"},
                {"type": "date", "key": "geboortedatum"},
                {"type": "signature", "key": "signature"},
            ],
            submitted_data={
                "adres": "Voorburg",
                "voornaam": "shea",
                "familienaam": "meyers",
            },
            completed=True,
        )

        cls.submission_step_1 = cls.submission_1.steps[0]

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    def test_displaying_merged_data_formio_formatters(self):
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )
        expected = """
        <ul>
        <li>adres: Voorburg</li>
        <li>voornaam: shea</li>
        <li>familienaam: meyers</li>
        <li>geboortedatum: None</li>
        <li>signature: None</li>
        </ul>
        """

        self.assertContains(response, expected, html=True)

    def test_displaying_merged_data_displays_signature_as_image_formio_formatters(self):
        form_variable = FormVariable.objects.get(
            key="signature", form=self.submission_1.form
        )
        SubmissionValueVariableFactory.create(
            key="signature",
            submission=self.submission_1,
            value="data:image/png;base64,iVBOR",
            form_variable=form_variable,
        )

        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            "<li>signature: <img class='signature-image' src='data:image/png;base64,iVBOR' alt='signature'></li>",
            html=True,
        )

    def test_viewing_submission_details_in_admin_creates_log(self):
        self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_admin.txt"
            ).count(),
            1,
        )

    @patch("openforms.submissions.admin.on_post_submission_event")
    def test_retry_processing_submissions_only_resends_failed_submissions(
        self, mock_on_post_submission_event
    ):
        failed = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        not_failed = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [str(failed.pk), str(not_failed.pk)]

        form.submit()

        mock_on_post_submission_event.assert_called_once_with(
            failed.id, PostSubmissionEvents.on_retry
        )

    @patch("openforms.submissions.admin.on_post_submission_event")
    def test_retry_processing_submissions_resends_all_failed_submissions(
        self, mock_on_post_submission_event
    ):
        failed = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        failed_needs_retry = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.failed,
        )
        pending = SubmissionFactory.create(
            needs_on_completion_retry=False,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )
        pending_needs_retry = SubmissionFactory.create(
            needs_on_completion_retry=True,
            completed=True,
            registration_status=RegistrationStatuses.pending,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [
            str(failed.pk),
            str(failed_needs_retry.pk),
            str(pending.pk),
            str(pending_needs_retry.pk),
        ]

        form.submit()

        mock_on_post_submission_event.assert_any_call(
            failed.id, PostSubmissionEvents.on_retry
        )
        mock_on_post_submission_event.assert_any_call(
            failed_needs_retry.id, PostSubmissionEvents.on_retry
        )
        self.assertEqual(mock_on_post_submission_event.call_count, 2)

    @patch("openforms.submissions.admin.on_post_submission_event")
    @patch("openforms.registrations.tasks.GlobalConfiguration.get_solo")
    def test_retry_processing_submissions_resets_submission_registration_attempts(
        self, mock_get_solo, mock_on_post_submission_event
    ):
        mock_get_solo.return_value = GlobalConfiguration(registration_attempt_limit=5)

        failed_above_limit = SubmissionFactory.create(
            completed=True,
            registration_status=RegistrationStatuses.failed,
            registration_attempts=10,
        )
        failed_below_limit = SubmissionFactory.create(
            completed=True,
            registration_status=RegistrationStatuses.failed,
            registration_attempts=2,
        )

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "retry_processing_submissions"
        form["_selected_action"] = [
            str(failed_above_limit.pk),
            str(failed_below_limit.pk),
        ]

        form.submit()

        mock_on_post_submission_event.assert_any_call(
            failed_above_limit.id, PostSubmissionEvents.on_retry
        )
        mock_on_post_submission_event.assert_any_call(
            failed_below_limit.id, PostSubmissionEvents.on_retry
        )
        self.assertEqual(mock_on_post_submission_event.call_count, 2)

        failed_above_limit.refresh_from_db()
        failed_below_limit.refresh_from_db()

        self.assertEqual(failed_above_limit.registration_attempts, 0)
        self.assertEqual(failed_below_limit.registration_attempts, 0)

    def test_change_view_displays_logs_if_not_avg(self):
        # add regular submission log
        submission_start(self.submission_1)

        # viewing this generates an AVG log
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )
        start_log, avg_log = TimelineLogProxy.objects.order_by("pk")

        # regular log visible
        self.assertContains(response, start_log.get_message())

        # avg log not visible
        self.assertNotContains(response, avg_log.get_message())

    def test_change_view_doesnt_display_logic_log(self):
        rule = FormLogicFactory(
            form=self.submission_1.form,
            json_logic_trigger={"==": [{"var": "voornaam"}, "test"]},
            actions=[],
        )
        merged_data = self.submission_1.get_merged_data()

        logic.log_logic_evaluation(
            self.submission_1,
            [EvaluatedRule(rule=cast(FormLogic, rule), triggered=False)],
            merged_data,
            merged_data,
        )

        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        logic_logs = TimelineLogProxy.objects.filter(
            template="logging/events/submission_logic_evaluated.txt"
        )

        self.assertEqual(1, len(logic_logs))

        self.assertNotContains(response, logic_logs[0].get_message())

    def test_search(self):
        list_url = furl(reverse("admin:submissions_submission_changelist"))
        list_url.args["q"] = "some value"

        response = self.app.get(
            list_url.url,
            user=self.user,
        )

        self.assertEqual(200, response.status_code)


@disable_2fa
class LogicLogsAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = SubmissionFactory.from_data(
            {
                "firstname": "foo",
                "birthdate": "2022-06-20",
            },
        )

        cls.staff_with_permission = StaffUserFactory.create(
            user_permissions=["submissions.view_submission"]
        )

    def test_user_without_permission_view(self):
        user_without_permission = UserFactory.create()

        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=user_without_permission,
            status=status.HTTP_403_FORBIDDEN,
        )

    def test_user_with_permission_view(self):
        user_with_permission = UserFactory.create(
            user_permissions=["submissions.view_submission"]
        )

        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=user_with_permission,
            status=status.HTTP_403_FORBIDDEN,
        )

    def test_user_staff_with_permission_view(self):
        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.staff_with_permission,
            status=status.HTTP_200_OK,
        )

    def test_user_staff_without_permission_view(self):
        staff_without_permission = StaffUserFactory.create()

        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=staff_without_permission,
            status=status.HTTP_403_FORBIDDEN,
        )

    def test_submission_logs_evaluated_logic_view_with_rules(self):

        date_compared = "2022-06-20"
        operator = ">"
        json_logic_trigger = {
            operator: [{"date": {"var": "birthdate"}}, {"date": date_compared}]
        }

        rule = FormLogicFactory(
            form=self.submission.form,
            json_logic_trigger=json_logic_trigger,
            actions=[],
        )
        merged_data = self.submission.get_merged_data()

        logic.log_logic_evaluation(
            self.submission,
            [EvaluatedRule(rule=cast(FormLogic, rule), triggered=False)],
            merged_data,
            merged_data,
        )

        response = self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.staff_with_permission,
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertContains(response, "birthdate")
        self.assertContains(response, operator)
        self.assertContains(response, date_compared)

    def test_submission_logs_evaluated_logic_view_without_rule(self):
        response = self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.staff_with_permission,
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertContains(response, _("No logic rules for that submission"))

    def test_delete_submission_without_logs(self):
        submission = SubmissionFactory.create(completed_on=timezone.now())
        user = SuperUserFactory.create()

        url = reverse("admin:submissions_submission_changelist")
        changelist = self.app.get(url, user=user)

        html_form = changelist.forms["changelist-form"]
        html_form["action"] = "delete_selected"
        html_form["_selected_action"] = [submission.pk]

        confirmation_page = html_form.submit()

        self.assertEqual(1, len(confirmation_page.forms))

        confirmation_form = confirmation_page.forms[0]
        confirmation_form["_selected_action"] = [submission.pk]
        confirmation_form["action"] = "delete_selected"
        confirmation_form["post"] = "yes"

        delete_response = confirmation_form.submit()

        self.assertRedirects(delete_response, url)
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())

    def test_delete_submission_with_logs_superuser(self):
        submission = SubmissionFactory.create(completed_on=timezone.now())
        user = SuperUserFactory.create()
        logevent.submission_details_view_admin(submission, user)

        url = reverse("admin:submissions_submission_changelist")
        changelist = self.app.get(url, user=user)

        html_form = changelist.forms["changelist-form"]
        html_form["action"] = "delete_selected"
        html_form["_selected_action"] = [submission.pk]

        confirmation_page = html_form.submit()

        self.assertEqual(1, len(confirmation_page.forms))

        confirmation_form = confirmation_page.forms[0]
        confirmation_form["_selected_action"] = [submission.pk]
        confirmation_form["action"] = "delete_selected"
        confirmation_form["post"] = "yes"

        delete_response = confirmation_form.submit()

        self.assertRedirects(delete_response, url)
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())
