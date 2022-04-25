from decimal import Decimal

from django.test import TestCase

from freezegun import freeze_time

from openforms.submissions.tests.factories import SubmissionFactory

from ...config.models import GlobalConfiguration
from ..constants import PaymentStatus
from ..models import SubmissionPayment
from .factories import SubmissionPaymentFactory


class SubmissionPaymentTests(TestCase):
    @freeze_time("2020-01-01")
    def test_create_for(self):
        amount = Decimal("11.25")
        options = {
            "foo": 123,
        }
        config = GlobalConfiguration.get_solo()
        config.payment_order_id_prefix = ""
        config.save()

        submission = SubmissionFactory.create(
            form__payment_backend="plugin1",
            form__payment_backend_options=options,
        )
        # create some existent records
        SubmissionPaymentFactory.create(order_id=1)
        SubmissionPaymentFactory.create(order_id=2)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 3)
        self.assertEqual(payment.public_order_id, "000003")

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 4)
        self.assertEqual(payment.public_order_id, "000004")

        # check overflow over default 5 digit non-year part
        SubmissionPaymentFactory.create(order_id=10000000)

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 10000001)
        self.assertEqual(payment.public_order_id, "10000001")

    @freeze_time("2020-01-01")
    def test_create_for_with_prefix(self):
        amount = Decimal("11.25")
        options = {
            "foo": 123,
        }
        config = GlobalConfiguration.get_solo()
        config.payment_order_id_prefix = "xyz{year}"
        config.save()

        submission = SubmissionFactory.create(
            form__payment_backend="plugin1",
            form__payment_backend_options=options,
        )
        # create some existent records
        SubmissionPaymentFactory.create(order_id=1)
        SubmissionPaymentFactory.create(order_id=2)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 3)
        self.assertEqual(payment.public_order_id, "xyz2020000003")

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 4)
        self.assertEqual(payment.public_order_id, "xyz2020000004")

        # check overflow over default 5 digit non-year part
        SubmissionPaymentFactory.create(order_id=10000000)

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount
        )
        self.assertEqual(payment.order_id, 10000001)
        self.assertEqual(payment.public_order_id, "xyz202010000001")

    def test_queryset_sum_amount(self):
        self.assertEqual(0, SubmissionPayment.objects.none().sum_amount())

        SubmissionPaymentFactory.create(amount=Decimal("1"))
        SubmissionPaymentFactory.create(amount=Decimal("2"))
        SubmissionPaymentFactory.create(amount=Decimal("3"))
        self.assertEqual(6, SubmissionPayment.objects.sum_amount())

    def test_status_is_final(self):
        for s in [PaymentStatus.started, PaymentStatus.processing]:
            with self.subTest(s):
                self.assertNotIn(s, PaymentStatus.is_final)

        for s in [
            PaymentStatus.registered,
            PaymentStatus.completed,
            PaymentStatus.failed,
        ]:
            with self.subTest(s):
                self.assertIn(s, PaymentStatus.is_final)
