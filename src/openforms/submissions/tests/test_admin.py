from unittest.mock import patch

from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy

from ..constants import RegistrationStatuses
from .factories import SubmissionFactory


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

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_displaying_merged_data(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(enable_formio_formatters=False)
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

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_displaying_merged_data_formio_formatters(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(enable_formio_formatters=True)
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

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_displaying_merged_data_displays_signature_as_image(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(enable_formio_formatters=False)

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
