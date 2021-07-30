from decimal import Decimal

import factory

from openforms.payments.models import SubmissionPayment
from openforms.submissions.tests.factories import SubmissionFactory


class SubmissionPaymentFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)
    plugin_id = "demo"
    form_url = "http://test/form/url"
    order_id = "order-1234"
    amount = Decimal("10.00")

    class Meta:
        model = SubmissionPayment

    @classmethod
    def for_backend(cls, plugin_id, options=None, **kwargs):
        payment = SubmissionPaymentFactory.create(
            plugin_id=plugin_id,
            submission__form__payment_backend=plugin_id,
            submission__form__payment_backend_options=options or {"non-empty": True},
            **kwargs
        )
        return payment
