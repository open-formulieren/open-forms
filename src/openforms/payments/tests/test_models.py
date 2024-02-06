from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase

from freezegun import freeze_time

from openforms.config.models import GlobalConfiguration
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import PAYMENT_STATUS_FINAL, PaymentStatus
from ..models import SubmissionPayment
from .factories import SubmissionPaymentFactory


class SubmissionPaymentTests(TransactionTestCase):
    # We rely on the PK:
    reset_sequences = True

    def test_str(self):
        submission_payment = SubmissionPayment(
            public_order_id="10",
            status=PaymentStatus.completed,
        )

        self.assertEqual(
            str(submission_payment), f"#10 '{PaymentStatus.completed.label}' 0"
        )

    @patch(
        "openforms.payments.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(payment_order_id_prefix=""),
    )
    def test_create_for(self, m: MagicMock):
        amount = Decimal("11.25")
        options = {
            "foo": 123,
        }

        submission = SubmissionFactory.create(
            form__payment_backend="plugin1",
            form__payment_backend_options=options,
            public_registration_reference="OF-123456",
        )
        # create some pre-existing records
        SubmissionPaymentFactory.create_batch(size=2)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.public_order_id, "OF-123456/3")

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.public_order_id, "OF-123456/4")

    @freeze_time("2020-01-01")
    @patch(
        "openforms.payments.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(payment_order_id_prefix="xyz{year}"),
    )
    def test_create_for_with_prefix(self, m: MagicMock):
        amount = Decimal("11.25")
        options = {
            "foo": 123,
        }

        submission = SubmissionFactory.create(
            form__payment_backend="plugin1",
            form__payment_backend_options=options,
            public_registration_reference="OF-123456",
        )
        # create some pre-existing records
        SubmissionPaymentFactory.create_batch(size=2)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.public_order_id, "xyz2020/OF-123456/3")

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.public_order_id, "xyz2020/OF-123456/4")

    @patch(
        "openforms.payments.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            payment_order_id_prefix="", wait_for_payment_to_register=True
        ),
    )
    @patch(
        "openforms.submissions.public_references.get_random_reference",
        return_value="OF-123456",
    )
    def test_create_for_no_registration(self, m1: MagicMock, m2: MagicMock):
        amount = Decimal("11.25")
        options = {
            "foo": 123,
        }

        submission = SubmissionFactory.create(completed_not_preregistered=True)
        # create some pre-existing records
        SubmissionPaymentFactory.create_batch(size=2)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )

        self.assertEqual(payment.public_order_id, "OF-123456/3")

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.public_order_id, "OF-123456/4")

    def test_queryset_sum_amount(self):
        self.assertEqual(0, SubmissionPayment.objects.none().sum_amount())

        SubmissionPaymentFactory.create(amount=Decimal("1"))
        SubmissionPaymentFactory.create(amount=Decimal("2"))
        SubmissionPaymentFactory.create(amount=Decimal("3"))
        self.assertEqual(6, SubmissionPayment.objects.sum_amount())

    def test_status_is_final(self):
        for s in [PaymentStatus.started, PaymentStatus.processing]:
            with self.subTest(s):
                self.assertNotIn(s, PAYMENT_STATUS_FINAL)

        for s in [
            PaymentStatus.registered,
            PaymentStatus.completed,
            PaymentStatus.failed,
        ]:
            with self.subTest(s):
                self.assertIn(s, PAYMENT_STATUS_FINAL)
