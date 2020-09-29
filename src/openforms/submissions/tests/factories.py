import factory

from openforms.core.tests.factories import FormFactory

from ..models import Submission, SubmissionStep


class SubmissionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Submission

    form = factory.SubFactory(FormFactory)


class SubmissionStepFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SubmissionStep

    submission = factory.SubFactory(SubmissionFactory)
