import uuid
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from privates.test import temp_private_root

from openforms.appointments.tests.utils import setup_jcc
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.tests.factories import FormDefinitionFactory

from ..constants import RegistrationStatuses
from ..models import SubmissionReport, TemporaryFileUpload
from ..tasks import on_completion_retry, retry_processing_submissions
from ..tasks.appointments import AppointmentRegistrationAborted
from .factories import SubmissionFactory, SubmissionFileAttachmentFactory


class OnCompletionRetryTests(TestCase):
    pass


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
