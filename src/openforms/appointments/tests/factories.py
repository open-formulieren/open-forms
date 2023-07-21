from django.utils import timezone

import factory
import factory.fuzzy

from openforms.submissions.tests.factories import SubmissionFactory

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
    datetime = factory.Faker("future_datetime", tzinfo=timezone.utc)

    class Meta:
        model = "appointments.Appointment"


class AppointmentProductFactory(factory.django.DjangoModelFactory):
    appointment = factory.SubFactory(AppointmentFactory)
    product_id = factory.Sequence(lambda n: f"product-{n}")
    amount = factory.fuzzy.FuzzyInteger(low=1, high=5)

    class Meta:
        model = "appointments.AppointmentProduct"
