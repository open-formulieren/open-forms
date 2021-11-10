import factory

from openforms.forms.tests.factories import FormFactory


class ConfirmationEmailTemplateFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    content = "Thanks!"

    class Meta:
        model = "emails.ConfirmationEmailTemplate"

    @classmethod
    def create(cls, **kwargs):
        if "form" in kwargs:
            # Update the form to ensure this email is used for the form and
            #   not the one in the Global Configuration
            kwargs["form"].send_custom_confirmation_email = True
            kwargs["form"].save(update_fields=["send_custom_confirmation_email"])
        return super().create(**kwargs)
