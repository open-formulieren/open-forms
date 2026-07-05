from openforms.formio.utils import iter_components
from openforms.forms.api.serializers import FormDefinitionSerializer

from .base import BaseExportSerializer


class FormDefinitionExportSerializer(FormDefinitionSerializer, BaseExportSerializer):
    is_exporting = True

    def remove_sensitive_content(self, instance, representation):
        representation = super().remove_sensitive_content(instance, representation)

        if (form := self.context.get("form", None)) is None:
            return representation

        sensitive_variables = [
            registration.options["to_emails_from_variable"]
            for registration in form.registration_backends.all()
            if registration.backend == "email"
            and "to_emails_from_variable" in registration.options
        ]

        for component in iter_components(representation.get("configuration", {})):
            if component["key"] in sensitive_variables:
                component["defaultValue"] = ""

        return representation
