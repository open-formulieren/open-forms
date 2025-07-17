from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone

from privates.test import temp_private_root

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.registrations.exceptions import RegistrationFailed

from ..constants import PostSubmissionEvents, RegistrationStatuses
from ..tasks import on_post_submission_event, retry_processing_submissions
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
        zgw_group = ZGWApiGroupConfigFactory.create()
        # set up a complex submission, with an appointment and payment required.
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            # set by :func:`openforms.payments.tasks.update_submission_payment_status`
            needs_on_completion_retry=True,
            registration_success=True,
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            form__payment_backend="ogone-legacy",
            registration_result={
                "zaak": {
                    "url": "https://example.com",
                    "identificatie": "ZAAK-123",
                }
            },
            with_completed_payment=True,
        )
        assert submission.payment_required, "Form must require payment for this test"
        assert submission.payment_user_has_paid, (
            "Paid status should be True - the return view received the payment from Ogone."
        )
        original_register_date = submission.last_register_date
        appointment_info = AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )
        original_appointment_id = appointment_info.appointment_id

        with patch(
            "openforms.registrations.contrib.zgw_apis.client.ZakenClient.set_payment_status"
        ) as mock_set_payment_status:
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        appointment_info.refresh_from_db()
        # assert that we now no longer have to retry
        self.assertFalse(submission.needs_on_completion_retry)
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        self.assertEqual(appointment_info.appointment_id, original_appointment_id)
        mock_set_payment_status.assert_called_once_with(
            {
                "url": "https://example.com",
                "identificatie": "ZAAK-123",
            }
        )

    def test_payment_status_update_still_fails(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        # set up a complex submission, with an appointment and payment required.
        submission = SubmissionFactory.create(
            completed=True,
            # set by :func:`openforms.payments.tasks.update_submission_payment_status`
            needs_on_completion_retry=True,
            registration_success=True,
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            form__payment_backend="ogone-legacy",
            registration_result={
                "zaak": {
                    "url": "https://example.com",
                    "identificatie": "ZAAK-123",
                }
            },
            public_registration_reference="ZAAK-123",
            with_completed_payment=True,
        )
        assert submission.payment_required, "Form must require payment for this test"
        assert submission.payment_user_has_paid, (
            "Paid status should be True - the return view received the payment from Ogone."
        )
        original_register_date = submission.last_register_date
        appointment_info = AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
        )
        original_appointment_id = appointment_info.appointment_id

        # invoke the chain
        patcher = patch(
            "openforms.registrations.contrib.zgw_apis.client.ZakenClient.set_payment_status",
            side_effect=Exception("Something went wrong"),
        )
        with patcher as mock_set_payment_status, self.assertRaises(Exception):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        appointment_info.refresh_from_db()
        # assert that we now no longer have to retry
        self.assertTrue(submission.needs_on_completion_retry)
        # check that the registration did not run again (idemptotent, a side effect is
        # that last_register_date is updated if it runs)
        self.assertEqual(submission.last_register_date, original_register_date)
        self.assertEqual(appointment_info.appointment_id, original_appointment_id)
        mock_set_payment_status.assert_called_once_with(
            {
                "url": "https://example.com",
                "identificatie": "ZAAK-123",
            }
        )


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCompletionRetryFailedRegistrationTests(TestCase):
    """
    Test the various retry branches if the backend registration failed.
    """

    @patch("openforms.payments.tasks.update_submission_payment_registration")
    def test_backend_registration_still_fails(self, mock_update_payment):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            # registration failed, so an internal reference was created
            public_registration_reference="OF-1234",
        )
        original_register_date = submission.last_register_date

        registration_patcher = patch(
            "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission",
            side_effect=RegistrationFailed("still failing"),
        )

        with (
            registration_patcher as mock_register,
            self.assertRaises(RegistrationFailed),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        mock_register.assert_called_once()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_not_called()
        self.assertNotEqual(submission.last_register_date, original_register_date)
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertTrue(submission.needs_on_completion_retry)

    @patch("openforms.payments.tasks.update_submission_payment_registration")
    def test_backend_preregistration_still_fails(self, mock_update_payment):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            needs_on_completion_retry=True,
            pre_registration_completed=False,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
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
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        mock_preregister.assert_called_once()
        mock_register.assert_not_called()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_not_called()
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertTrue(submission.needs_on_completion_retry)

    @patch(
        "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.update_payment_status"
    )
    def test_backend_registration_succeeds(self, mock_update_payment):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            completed=True,
            needs_on_completion_retry=True,
            registration_failed=True,
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
                "product_url": "http://example.com",
            },
            # registration failed, so an internal reference was created
            public_registration_reference="OF-1234",
            with_completed_payment=True,
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
            on_post_submission_event(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        mock_register.assert_called_once()
        # downstream tasks should not have been called - chain should abort
        mock_update_payment.assert_called_once_with(
            submission,
            {
                "zgw_api_group": zgw_group,
                "case_type_identification": "",
                "document_type_description": "",
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
                "product_url": "http://example.com",
                "partners_description": "",
                "partners_roltype": "",
            },
        )
        self.assertNotEqual(submission.last_register_date, original_register_date)
        self.assertEqual(submission.public_registration_reference, "OF-1234")
        self.assertFalse(submission.needs_on_completion_retry)
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)


class RetrySubmissionTest(TestCase):
    @patch("openforms.submissions.tasks.on_post_submission_event")
    def test_resend_submission_task_only_retries_certain_submissions(self, m):
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

        self.assertEqual(m.call_count, 1)
        m.assert_called_once_with(
            failed_within_time_limit.id, PostSubmissionEvents.on_retry
        )
