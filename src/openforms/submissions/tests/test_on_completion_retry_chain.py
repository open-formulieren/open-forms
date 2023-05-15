from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone

from privates.test import temp_private_root

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.exceptions import RegistrationFailed

from ..constants import RegistrationStatuses
from ..tasks import on_completion_retry, retry_processing_submissions
from .factories import SubmissionFactory


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCompletionRetryFailedUpdatePaymentStatusTests(TestCase):
    """
    Test the various retry branches if the payment status update failed.

    In this scenario, initial backend registration succeeded, but updating the payment
    status after payment confirmation failed.

    The retry workflow may not register the submission with the backend again, nor may
    it do anything appointment related.
    """

    def test_payment_status_update_now_succeeds(self):
        # set up a complex submission, with an appointment and payment required.
        submission = SubmissionFactory.create(
            completed=True,
            # set by :func:`openforms.payments.tasks.update_submission_payment_status`
            needs_on_completion_retry=True,
            registration_success=True,
            pre_registration_completed=True,
            form__registration_backend="zgw-create-zaak",
            form__payment_backend="ogone-legacy",
            registration_result={
                "zaak": {
                    "url": "https://example.com",
                    "identificatie": "ZAAK-123",
                }
            },
            public_registration_reference="ZAAK-123",
        )
        # status simulates that we received the payment paid event from the payment provider
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )
        assert submission.payment_required, "Form must require payment for this test"
        assert (
            submission.payment_user_has_paid
        ), "Paid status should be True - the return view received the payment from Ogone."
        original_register_date = submission.last_register_date
        appointment_info = AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )
        original_appointment_id = appointment_info.appointment_id

        # invoke the chain
        with patch(
            "openforms.registrations.contrib.zgw_apis.plugin.set_zaak_payment"
        ) as mock_set_zaak_payment:
            on_completion_retry(submission.id)()

        submission.refresh_from_db()
        appointment_info.refresh_from_db()
        # assert that we now no longer have to retry
        self.assertFalse(submission.needs_on_completion_retry)
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        self.assertEqual(appointment_info.appointment_id, original_appointment_id)
        mock_set_zaak_payment.assert_called_once_with("https://example.com")

    def test_payment_status_update_still_fails(self):
        # set up a complex submission, with an appointment and payment required.
        submission = SubmissionFactory.create(
            completed=True,
            # set by :func:`openforms.payments.tasks.update_submission_payment_status`
            needs_on_completion_retry=True,
            pre_registration_completed=True,
            registration_success=True,
            form__registration_backend="zgw-create-zaak",
            form__payment_backend="ogone-legacy",
            registration_result={
                "zaak": {
                    "url": "https://example.com",
                    "identificatie": "ZAAK-123",
                }
            },
            public_registration_reference="ZAAK-123",
        )
        # status simulates that we received the payment paid event from the payment provider
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )
        assert submission.payment_required, "Form must require payment for this test"
        assert (
            submission.payment_user_has_paid
        ), "Paid status should be True - the return view received the payment from Ogone."
        original_register_date = submission.last_register_date
        appointment_info = AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )
        original_appointment_id = appointment_info.appointment_id

        # invoke the chain
        patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.set_zaak_payment",
            side_effect=Exception("Something went wrong"),
        )
        with patcher as mock_set_zaak_payment, self.assertRaises(Exception):
            on_completion_retry(submission.id)()

        submission.refresh_from_db()
        appointment_info.refresh_from_db()
        # assert that we now no longer have to retry
        self.assertTrue(submission.needs_on_completion_retry)
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        self.assertEqual(appointment_info.appointment_id, original_appointment_id)
        mock_set_zaak_payment.assert_called_once_with("https://example.com")


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCompletionRetryFailedRegistrationTests(TestCase):
    """
    Test the various retry branches if the backend registration failed.
    """

    @patch("openforms.payments.tasks.update_submission_payment_registration")
    def test_backend_registration_still_fails(self, mock_update_payment):
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            pre_registration_completed=True,
            # registration failed, so an internal reference was created
            public_registration_reference="OF-1234",
        )
        original_register_date = submission.last_register_date

        registration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission",
            side_effect=RegistrationFailed("still failing"),
        )

        with registration_patcher as mock_register, self.assertRaises(
            RegistrationFailed
        ):
            # invoke the chain
            on_completion_retry(submission.id)()

        submission.refresh_from_db()
        mock_register.assert_called_once()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_not_called()
        self.assertNotEqual(submission.last_register_date, original_register_date)
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertTrue(submission.needs_on_completion_retry)

    @patch("openforms.payments.tasks.update_submission_payment_registration")
    def test_backend_preregistration_still_fails(self, mock_update_payment):
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            pre_registration_completed=False,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            # registration failed, so an internal reference was created
            public_registration_reference="OF-1234",
        )

        preregistration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
            side_effect=RegistrationFailed("still failing"),
        )
        registration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission",
            side_effect=RegistrationFailed("still failing"),
        )

        with (
            preregistration_patcher as mock_preregister,
            registration_patcher as mock_register,
            self.assertRaises(RegistrationFailed),
        ):
            # invoke the chain
            on_completion_retry(submission.id)()

        submission.refresh_from_db()
        mock_preregister.assert_called_once()
        mock_register.assert_not_called()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_not_called()
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertTrue(submission.needs_on_completion_retry)

    @patch("openforms.payments.tasks.update_submission_payment_registration")
    def test_backend_registration_succeeds(self, mock_update_payment):
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            # registration failed, so an internal reference was created
            public_registration_reference="OF-1234",
        )
        AppointmentInfoFactory.create(submission=submission, registration_ok=True)
        original_register_date = submission.last_register_date

        preregistration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
        )
        registration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission",
            return_value={
                "zaak": {
                    "url": "https://example.com",
                    "identificatie": "ZAAK-123",
                }
            },
        )

        with preregistration_patcher, registration_patcher as mock_register:
            # invoke the chain
            on_completion_retry(submission.id)()

        submission.refresh_from_db()
        mock_register.assert_called_once()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_called_once_with(submission)
        self.assertNotEqual(submission.last_register_date, original_register_date)
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertFalse(submission.needs_on_completion_retry)
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)


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
