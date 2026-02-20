from datetime import UTC

import factory
import factory.fuzzy

from openforms.submissions.tests.factories import SubmissionFactory

from ..base import Product
from ..constants import AppointmentDetailsStatus
from ..models import AppointmentInfo


class AppointmentInfoFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = AppointmentInfo

    class Params:
        has_missing_info = factory.Trait(
            status=AppointmentDetailsStatus.missing_info,
            appointment_id="",
            error_information="Some fields are missing.",
        )
        registration_ok = factory.Trait(
            status=AppointmentDetailsStatus.success,
            appointment_id=factory.Sequence(lambda n: f"appointment-{n}"),
            error_information="",
        )
        registration_failed = factory.Trait(
            status=AppointmentDetailsStatus.failed,
            appointment_id="",
            error_information="Failed to make appointment",
        )


class AppointmentFactory(factory.django.DjangoModelFactory):
    plugin = "demo"
    submission = factory.SubFactory(SubmissionFactory, form__is_appointment_form=True)
    location = "some-location-id"
    datetime = factory.Faker("future_datetime", tzinfo=UTC)

    class Meta:
        model = "appointments.Appointment"

    @factory.post_generation
    def products(obj, create, extracted: list[Product], **kwargs):
        if not create:
            raise RuntimeError("You may only provide products with the create strategy")
        if not extracted:
            return

        for product in extracted:
            AppointmentProductFactory.create(
                appointment=obj,
                product_id=product.identifier,
                amount=product.amount,
            )

    @factory.post_generation
    def appointment_info(obj, create, extracted, **kwargs):
        if not create:
            raise RuntimeError(
                "You may only provide appointment info with the create strategy"
            )
        if not kwargs:
            return
        AppointmentInfoFactory.create(submission=obj.submission, **kwargs)


class AppointmentProductFactory(factory.django.DjangoModelFactory):
    appointment = factory.SubFactory(AppointmentFactory)
    product_id = factory.Sequence(lambda n: f"product-{n}")
    amount = factory.fuzzy.FuzzyInteger(low=1, high=5)

    class Meta:
        model = "appointments.AppointmentProduct"
