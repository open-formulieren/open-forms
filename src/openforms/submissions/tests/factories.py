import factory

from openforms.forms.tests.factories import FormFactory

from ..models import ConfirmationEmailTemplate, Submission, SubmissionStep


class SubmissionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Submission


class SubmissionStepFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory(SubmissionFactory)

    class Meta:
        model = SubmissionStep


class ConfirmationEmailTemplateFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = ConfirmationEmailTemplate
