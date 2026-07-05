from openforms.forms.api.serializers import FormVariableSerializer

from .base import BaseExportSerializer


class FormVariableExportSerializer(FormVariableSerializer, BaseExportSerializer):
    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)
        form = instance.form

        for registration in form.registration_backends.all():
            if (
                registration.backend == "email"
                and "to_emails_from_variable" in registration.options
                and registration.options["to_emails_from_variable"]
                == representation["key"]
            ):
                representation["initial_value"] = ""
                return representation

        return representation
