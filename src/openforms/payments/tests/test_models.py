from decimal import Decimal

from django.test import TestCase

from openforms.payments.models import SubmissionPayment
from openforms.submissions.tests.factories import SubmissionFactory


class SubmissionPaymentTests(TestCase):
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
        payment = SubmissionPayment.objects.create_for(
            submission, "plugin1", options, amount, form_url
        )

        # basic check
        self.assertTrue(bool(payment.order_id))
        self.assertTrue(str(payment))
