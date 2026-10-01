from ...api.serializers import FormVariableSerializer
from ...models import FormVariable
from ..constants import FormConfigurationOptions
from ..typing import FormConfigurationCleanup, FormVariableExportRepresentation
from .base import BaseExportSerializer


def remove_prefill_from_variable(representation: FormVariableExportRepresentation):
    representation["prefill_plugin"] = ""
    representation["prefill_attribute"] = ""
    representation["prefill_options"] = {}


class FormVariableExportSerializer(
    FormVariableSerializer,
    BaseExportSerializer[FormVariable, FormVariableExportRepresentation],
):
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup(
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_variable,
        ),
    )
    safe_export_fields = (
        "form",
        "form_definition",
        "name",
        "key",
        "source",
        "service_fetch_configuration",
        "prefill_plugin",
        "prefill_attribute",
        "prefill_identifier_role",
        "prefill_options",
        "data_type",
        "data_format",
        "is_sensitive_data",
        "initial_value",
    )

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
