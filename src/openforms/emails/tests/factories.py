import factory

from openforms.forms.tests.factories import FormFactory


class ConfirmationEmailTemplateFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = "emails.ConfirmationEmailTemplate"
