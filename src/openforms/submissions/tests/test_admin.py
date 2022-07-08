from unittest.mock import patch

from django.urls import reverse

from django_webtest import WebTest
from rest_framework import status

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.models import FormLogic
from openforms.logging import logevent
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy

from ...forms.models import FormVariable
from ..constants import RegistrationStatuses
from .factories import SubmissionFactory, SubmissionValueVariableFactory
from .mixins import VariablesTestMixin


class TestSubmissionAdmin(VariablesTestMixin, WebTest):
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

    @patch("openforms.submissions.admin.on_completion_retry")
    def test_retry_processing_submissions_only_resends_failed_submissions(
        self, on_completion_retry_mock
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

        on_completion_retry_mock.assert_called_once_with(failed.id)
        on_completion_retry_mock.return_value.delay.assert_called_once()

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
        start_log, avg_log = TimelineLogProxy.objects.all()

        # regular log visible
        self.assertContains(response, start_log.get_message())

        # avg log not visible
        self.assertNotContains(response, avg_log.get_message())


class TestLogicEvaluated(VariablesTestMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.from_data(
            {
                "firstname": "foo",
                "birthdate": "2022-06-20",
            },
        )

    def setUp(self):
        super().setUp()
        self.admin_user = UserFactory.create(
            is_superuser=True, is_staff=True, app=self.app
        )
        self.anonymous_user = UserFactory.create(
            is_superuser=False, is_staff=False, app=self.app
        )

    def test_invalid_permission_view(self):
        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.anonymous_user,
            status=status.HTTP_403_FORBIDDEN,
        )

    def test_valid_prmission_view(self):
        self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.admin_user,
            status=status.HTTP_200_OK,
        )

    def test_submission_logs_evaluated_logic_view(self):

        json_logic_trigger = {
            ">": [{"date": {"var": "birthdate"}}, {"date": "2022-06-20"}]
        }

        actions = [
            {
                "component": "firstname",
                "formStep": "",
                "action": {
                    "type": "property",
                    "property": {"value": "disabled", "type": "bool"},
                    "state": True,
                },
            }
        ]

        rule = FormLogic(
            form=self.submission.form,
            json_logic_trigger=json_logic_trigger,
            actions=actions,
        )
        logevent.submission_logic_evaluated(
            self.submission, [{"rule": rule, "trigger": True}]
        )

        response = self.app.get(
            reverse("admin:logs-evaluated-logic", args=(self.submission.pk,)),
            user=self.admin_user,
        )

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertContains(response, self.submission)
