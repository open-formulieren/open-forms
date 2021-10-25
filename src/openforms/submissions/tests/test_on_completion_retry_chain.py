import uuid
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from privates.test import temp_private_root

from openforms.appointments.service import AppointmentUpdateFailed
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.tests.factories import FormDefinitionFactory

from ..constants import RegistrationStatuses
from ..models import SubmissionReport, TemporaryFileUpload
from ..tasks import on_completion_retry, retry_processing_submissions
from ..tasks.appointments import AppointmentRegistrationAborted
from .factories import SubmissionFactory, SubmissionFileAttachmentFactory


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCompletionRetryFailedUpdateAppointmentTests(TestCase):
    """
    Test the various retry branches if the appointment update failed.

    In this scenario, initial backend registration succeeded, but updating the
    appointment with those results failed.

    The retry workflow may not register the submission with the backend again,
    it may not register the appoinment again but it must try to update the appointment.
    """

    @patch("openforms.submissions.tasks.appointments.update_appointment")
    def test_update_succeeds(self, mock_update_appointment):
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_success=True,
            form__registration_backend="zgw-create-zaak",
            registration_result={
                "zaak": {
                    "identificatie": "ZAAK-123",
                }
            },
            public_registration_reference="ZAAK-123",
        )
        original_register_date = submission.last_register_date
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )

        # invoke the chain
        on_completion_retry(submission.id)()

        mock_update_appointment.assert_called_once_with(submission)
        submission.refresh_from_db()
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        self.assertFalse(submission.needs_on_completion_retry)

    @patch("openforms.submissions.tasks.appointments.update_appointment")
    def test_update_fails_again(self, mock_update_appointment):
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_success=True,
            form__registration_backend="zgw-create-zaak",
            registration_result={
                "zaak": {
                    "identificatie": "ZAAK-123",
                }
            },
            public_registration_reference="ZAAK-123",
        )
        original_register_date = submission.last_register_date
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )
        mock_update_appointment.side_effect = AppointmentUpdateFailed("nope")

        # invoke the chain
        chain = on_completion_retry(submission.id)
        with self.assertRaises(AppointmentUpdateFailed):
            chain()

        mock_update_appointment.assert_called_once_with(submission)
        submission.refresh_from_db()
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        # it failed again, so we must keep re-trying
        self.assertTrue(submission.needs_on_completion_retry)


class OnCompletionRetryFailedRegistrationTests(TestCase):
    """
    Test the various retry branches if the backend registration failed.
    """


class RetrySubmissionTest(TestCase):
    @patch("openforms.submissions.tasks.on_completion_retry")
    def test_resend_submission_task_only_retries_certain_submissions(self, mock_chain):
        failed_within_time_limit = SubmissionFactory.create(
            registration_failed=True,
            needs_on_completion_retry=True,
            completed_on=timezone.now(),
        )
        # Outside time limit
        SubmissionFactory.create(
            registration_failed=True,
            needs_on_completion_retry=True,
            completed_on=(
                timezone.now()
                - timedelta(hours=settings.RETRY_SUBMISSIONS_TIME_LIMIT + 1)
            ),
        )
        # Not failed
        SubmissionFactory.create(
            needs_on_completion_retry=False,
            registration_pending=False,
            completed_on=timezone.now(),
        )

        retry_processing_submissions()

        self.assertEqual(mock_chain.call_count, 1)
        mock_chain.assert_called_once_with(failed_within_time_limit.id)
        mock_chain.return_value.delay.assert_called_once_with()
