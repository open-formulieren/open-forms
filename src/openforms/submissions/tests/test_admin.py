from unittest.mock import patch

from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.logging.logevent import submission_start
from openforms.logging.models import TimelineLogProxy

from ...config.models import GlobalConfiguration
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

    @patch("openforms.submissions.admin.on_completion_retry")
    def test_retry_processing_submissions_resends_all_failed_submissions(
        self, on_completion_retry_mock
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

        on_completion_retry_mock.assert_any_call(failed.id)
        on_completion_retry_mock.assert_any_call(failed_needs_retry.id)
        self.assertEqual(on_completion_retry_mock.return_value.delay.call_count, 2)

    @patch("openforms.submissions.admin.on_completion_retry")
    @patch("openforms.registrations.tasks.GlobalConfiguration.get_solo")
    def test_retry_processing_submissions_resets_submission_registration_attempts(
        self, mock_get_solo, on_completion_retry_mock
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

        on_completion_retry_mock.assert_any_call(failed_above_limit.id)
        on_completion_retry_mock.assert_any_call(failed_below_limit.id)
        self.assertEqual(on_completion_retry_mock.return_value.delay.call_count, 2)

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
        start_log, avg_log = TimelineLogProxy.objects.all()

        # regular log visible
        self.assertContains(response, start_log.get_message())

        # avg log not visible
        self.assertNotContains(response, avg_log.get_message())
