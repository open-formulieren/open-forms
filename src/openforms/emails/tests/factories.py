import factory

from openforms.forms.tests.factories import FormFactory


class ConfirmationEmailTemplateFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    content = "Thanks!"

    class Meta:
        model = "emails.ConfirmationEmailTemplate"
