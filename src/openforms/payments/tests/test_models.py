from decimal import Decimal

from django.test import TestCase

from freezegun import freeze_time

from openforms.payments.models import SubmissionPayment
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory


class SubmissionPaymentTests(TestCase):
    @freeze_time("2020-01-01")
    def test_create_for(self):
        amount = Decimal("11.25")
        form_url = "http://test/form"
        options = {
            "foo": 123,
        }
        submission = SubmissionFactory.create(
            form__payment_backend="plugin1",
            form__payment_backend_options=options,
        )
        SubmissionPaymentFactory.create(order_id=202000001)
        SubmissionPaymentFactory.create(order_id=202000002)

        # create payment with auto-generated order_id
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount, form_url
        )
        self.assertEqual(payment.order_id, 202000003)
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount, form_url
        )
        self.assertEqual(payment.order_id, 202000004)

        # check overflow over default 5 digit non-year part
        SubmissionPaymentFactory.create(order_id=202012345678)

        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount, form_url
        )
        self.assertEqual(payment.order_id, 202012345679)

    def test_queryset_sum_amount(self):
        self.assertEqual(0, SubmissionPayment.objects.none().sum_amount())

        SubmissionPaymentFactory.create(amount=Decimal("1"))
        SubmissionPaymentFactory.create(amount=Decimal("2"))
        SubmissionPaymentFactory.create(amount=Decimal("3"))
        self.assertEqual(6, SubmissionPayment.objects.sum_amount())
