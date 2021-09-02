import factory

from openforms.submissions.tests.factories import SubmissionFactory

from ..models import AppointmentInfo


class AppointmentInfoFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = AppointmentInfo
