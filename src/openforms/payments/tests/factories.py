from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import factory
import faker

from openforms.config.models import GlobalConfiguration
from openforms.submissions.tests.factories import SubmissionFactory

from ..models import SubmissionPayment, SubmissionPaymentManager


def mocked_create_public_order_id_for(
    payment: SubmissionPayment, create: bool, extracted: str | None, **kwargs: Any
) -> None:
    if extracted is not None:
        payment.public_order_id = extracted
        return

    fake = faker.Faker()

    with patch(
        "openforms.payments.models.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(),
    ):
        pk = fake.random_int() if not create else None
        payment.public_order_id = SubmissionPaymentManager.create_public_order_id_for(
            payment, pk=pk
        )


class SubmissionPaymentFactory(factory.django.DjangoModelFactory):
    created = datetime.now()
    submission = factory.SubFactory(
        SubmissionFactory, with_public_registration_reference=True
    )
    plugin_id = "demo"
    plugin_options = {"foo": 123}
    amount = Decimal("10.00")
    public_order_id = factory.PostGeneration(mocked_create_public_order_id_for)

    class Meta:
        model = SubmissionPayment

    @classmethod
    def for_backend(cls, plugin_id, options=None, **kwargs):
        options = options or {"non-empty": True}
        payment = cls.create(
            plugin_id=plugin_id,
            plugin_options=options,
            submission__form__payment_backend=plugin_id,
            submission__form__payment_backend_options=options,
            **kwargs,
        )
        return payment

    @classmethod
    def for_submission(cls, submission, **kwargs):
        payment = cls.create(
            submission=submission,
            plugin_id=submission.form.payment_backend,
            plugin_options=submission.form.payment_backend_options,
            amount=submission.price,
            **kwargs,
        )
        return payment
