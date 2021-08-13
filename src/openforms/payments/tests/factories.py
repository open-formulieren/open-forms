from decimal import Decimal

import factory

from openforms.payments.models import SubmissionPayment
from openforms.submissions.tests.factories import SubmissionFactory


class SubmissionPaymentFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)
    plugin_id = "demo"
    plugin_options = {"foo": 123}
    form_url = "http://test/form/url"
    order_id = factory.Sequence(lambda n: int(f"2020{n:05}"))
    amount = Decimal("10.00")

    class Meta:
        model = SubmissionPayment

    @classmethod
    def for_backend(cls, plugin_id, options=None, **kwargs):
        options = options or {"non-empty": True}
        payment = SubmissionPaymentFactory.create(
            plugin_id=plugin_id,
            plugin_options=options,
            submission__form__payment_backend=plugin_id,
            submission__form__payment_backend_options=options,
            **kwargs,
        )
        return payment
