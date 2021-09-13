import factory

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
