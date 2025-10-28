import factory

from openforms.forms.tests.factories import FormFactory


class ConfirmationEmailTemplateFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    content = "Thanks!"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = "emails.ConfirmationEmailTemplate"

    class Params:
        with_tags = factory.Trait(
            subject="Hello",
            content="Thanks! {% payment_information %} {% appointment_information %} {% cosign_information %}",
        )
