import factory

from openforms.forms.constants import ConfirmationEmailOptions
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
            kwargs[
                "form"
            ].confirmation_email_option = ConfirmationEmailOptions.form_specific_email
            kwargs["form"].save(update_fields=["confirmation_email_option"])
        return super().create(**kwargs)
