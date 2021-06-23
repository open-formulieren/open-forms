import factory

from openforms.forms.tests.factories import FormFactory

from ..models import Submission, SubmissionReport, SubmissionStep


class SubmissionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Submission


class SubmissionStepFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionStep


class SubmissionReportFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("bs")
    content = factory.django.FileField(filename="submission_report.pdf")
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionReport
