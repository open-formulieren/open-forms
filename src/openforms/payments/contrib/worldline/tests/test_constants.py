from django.test import SimpleTestCase

from openforms.payments.contrib.worldline.constants import (
    HostedCheckoutStatus,
    PaymentStatus,
)


class HostedCheckoutStatusTests(SimpleTestCase):
    def test_to_payment_status(self):
        payment_status = HostedCheckoutStatus.to_payment_status(
            HostedCheckoutStatus.in_progress
        )

        self.assertEqual(payment_status, PaymentStatus.created)
