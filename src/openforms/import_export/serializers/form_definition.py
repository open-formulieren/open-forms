from openforms.formio.utils import iter_components
from openforms.forms.api.serializers import FormDefinitionSerializer
from openforms.import_export.typing import (
    FormConfigurationCleanup,
    FormConfigurationOptions,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.typing import JSONObject

from .base import BaseExportSerializer


def remove_prefill_from_component_configuration(representation: JSONObject):
    for component in representation.get("configuration", {}).get("components", []):
        if "prefill" not in component:
            return
        component["prefill"]["plugin"] = ""
        component["prefill"]["attribute"] = ""
        component["prefill"]["identifier_role"] = IdentifierRoles.main


class FormDefinitionExportSerializer(FormDefinitionSerializer, BaseExportSerializer):
    is_exporting = True
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup(
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_component_configuration,
        ),
    )

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
