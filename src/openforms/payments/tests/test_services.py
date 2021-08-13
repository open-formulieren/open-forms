from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from rest_framework import serializers

from openforms.payments.constants import PaymentStatus
from openforms.payments.services import update_submission_payment_registration
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.base import BasePlugin
from openforms.registrations.registry import Registry
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory


class Plugin(BasePlugin):
    configuration_options = serializers.Serializer()

    def update_payment_status(self, submission: Submission):
        pass


class UpdatePaymentTests(TestCase):
    def setUp(self):
        register = Registry()
        register("registration1")(Plugin)
        self.plugin = register["registration1"]

        registry_patch = patch("openforms.payments.services.register", new=register)
        registry_patch.start()
        self.addCleanup(registry_patch.stop)

    def create_payment(self, **kwargs):
        complete_kwargs = self.good_factory_kwargs()
        complete_kwargs.update(kwargs)
        return SubmissionPaymentFactory.create(**complete_kwargs)

    def good_factory_kwargs(self):
        # these together would update
        return dict(
            submission__registration_status=RegistrationStatuses.success,
            submission__registration_id="123",
            submission__form__registration_backend="registration1",
            submission__form__payment_backend="payment1",
            submission__form__product__price=Decimal("11.35"),
            status=PaymentStatus.completed,
            plugin_id="payment1",  # not used but added for completion
        )

    def bad_factory_kwargs(self):
        # all of these would individually block the update
        return dict(
            submission__registration_status=RegistrationStatuses.failed,
            submission__registration_id="",
            submission__form__registration_backend="",
            submission__form__payment_backend="",
            submission__form__product__price=Decimal("0"),
            status=PaymentStatus.failed,
            # plugin_id="",  # not used
        )

    def test_submission_default(self):
        # check with in-complete submission
        submission = SubmissionFactory.create()

        self.assertEqual(False, submission.payment_required)
        self.assertEqual(False, submission.payment_user_has_paid)
        self.assertEqual(False, submission.payment_registered)

        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_not_called()

    def test_submission_complete(self):
        # setup complete payment
        payment = self.create_payment()
        submission = payment.submission

        self.assertEqual(True, submission.payment_required)
        self.assertEqual(True, submission.payment_user_has_paid)
        self.assertEqual(False, submission.payment_registered)

        # now check if we update
        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_called_once_with(submission)

        payment.refresh_from_db()
        submission = payment.submission

        self.assertEqual(True, submission.payment_required)
        self.assertEqual(True, submission.payment_user_has_paid)
        self.assertEqual(True, submission.payment_registered)

        # check we don't update again
        with patch.object(self.plugin, "update_payment_status") as update_mock:
            update_submission_payment_registration(submission)
            update_mock.assert_not_called()

    def test_submission_bad(self):
        for key, value in self.bad_factory_kwargs().items():
            with self.subTest(key):
                payment = self.create_payment(**{key: value})
                submission = payment.submission

                # now check we don't update on these
                with patch.object(self.plugin, "update_payment_status") as update_mock:
                    update_submission_payment_registration(submission)
                    update_mock.assert_not_called()
