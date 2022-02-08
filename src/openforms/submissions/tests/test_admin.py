from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormDefinitionFactory, FormStepFactory
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy

from ..constants import RegistrationStatuses
from .factories import SubmissionFactory, SubmissionStepFactory


class TestSubmissionAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        form_definition = FormDefinitionFactory(
            configuration={
                "components": [
                    {"type": "textfield", "key": "adres"},
                    {"type": "textfield", "key": "voornaam"},
                    {"type": "textfield", "key": "familienaam"},
                    {"type": "date", "key": "geboortedatum"},
                    {"type": "signature", "key": "signature"},
                ]
            }
        )
        step = FormStepFactory.create(form_definition=form_definition)
        cls.submission_1 = SubmissionFactory.create(form=step.form)
        submission_2 = SubmissionFactory.create(
            form=step.form, completed_on=timezone.now()
        )
        cls.submission_step_1 = SubmissionStepFactory.create(
            submission=cls.submission_1,
            form_step=step,
            data={"adres": "Voorburg", "voornaam": "shea", "familienaam": "meyers"},
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=step,
            data={
                "voornaam": "shea",
                "familienaam": "meyers",
                "geboortedatum": "01-01-1991",
            },
        )

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    def test_displaying_merged_data(self):
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            "<ul><li>adres: Voorburg</li><li>voornaam: shea</li><li>familienaam: meyers</li></ul>",
            html=True,
        )

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_displaying_merged_data_formio_formatters(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(enable_formio_formatters=True)
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            "<ul><li>adres: Voorburg</li><li>voornaam: shea</li><li>familienaam: meyers</li></ul>",
            html=True,
        )

    def test_displaying_merged_data_displays_signature_as_image(self):
        self.submission_step_1.data["signature"] = "data:image/png;base64,iVBOR"
        self.submission_step_1.save()

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

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_displaying_merged_data_displays_signature_as_image_formio_formatters(
        self, mock_get_solo
    ):
        mock_get_solo.return_value = GlobalConfiguration(enable_formio_formatters=True)
        self.submission_step_1.data["signature"] = "data:image/png;base64,iVBOR"
        self.submission_step_1.save()

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
