from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from rest_framework import serializers

from openforms.registrations.base import BasePlugin
from openforms.registrations.registry import Registry
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import PaymentStatus
from ..services import update_submission_payment_registration
from .factories import SubmissionPaymentFactory


class Plugin(BasePlugin):
    configuration_options = serializers.Serializer()

    def register_submission(self, submission, options):
        pass

    def update_payment_status(self, submission: Submission):
        pass

    def get_reference_from_result(self, result):
        pass


class UpdatePaymentTests(TestCase):
    def setUp(self):
        super().setUp()
        register = Registry()
        register("registration1")(Plugin)
        self.plugin = register["registration1"]

        registry_patch = patch("openforms.payments.services.register", new=register)
        registry_patch.start()
        self.addCleanup(registry_patch.stop)

    def create_payment(self, **kwargs):
        good_kwargs = dict(
            # these together would update
            submission__registration_status=RegistrationStatuses.success,
            submission__form__registration_backend="registration1",
            submission__form__payment_backend="payment1",
            submission__form__product__price=Decimal("11.35"),
            status=PaymentStatus.completed,
            plugin_id="payment1",  # not used but added for completion
        )
        good_kwargs.update(kwargs)
        return SubmissionPaymentFactory.create(**good_kwargs)

    def test_submission_default(self):
        # check with incomplete submission
        submission = SubmissionFactory.create(completed=False)

        self.assertFalse(submission.payment_required)
        self.assertFalse(submission.payment_user_has_paid)
        self.assertFalse(submission.payment_registered)

        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_not_called()

    def test_submission_complete(self):
        # setup complete payment
        payment = self.create_payment()
        submission = payment.submission

        self.assertTrue(submission.payment_required)
        self.assertTrue(submission.payment_user_has_paid)
        self.assertFalse(submission.payment_registered)

        # now check if we update
        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_called_once_with(submission)

        payment.refresh_from_db()
        submission = payment.submission

        self.assertTrue(submission.payment_required)
        self.assertTrue(submission.payment_user_has_paid)
        self.assertTrue(submission.payment_registered)

        # check we don't update again
        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_not_called()

    def test_submission_bad(self):
        bad_factory_kwargs = dict(
            # all of these would individually block the update
            submission__registration_status=RegistrationStatuses.failed,
            submission__form__registration_backend="",
            submission__form__payment_backend="",
            submission__form__product__price=Decimal("0"),
            status=PaymentStatus.failed,
            # plugin_id="",  # not used
        )
        for key, value in bad_factory_kwargs.items():
            with self.subTest(key):
                payment = self.create_payment(**{key: value})
                submission = payment.submission

                # now check we don't update on these
                with patch.object(self.plugin, "update_payment_status") as update_mock:
                    update_submission_payment_registration(submission)
                    update_mock.assert_not_called()
