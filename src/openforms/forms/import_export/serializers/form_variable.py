from ...api.serializers import FormVariableSerializer
from ...models import FormVariable
from ..constants import FormConfigurationOptions
from ..datastructures import FormConfigurationCleanup
from ..typing import FormVariableDataRepresentation
from .base import BaseExportSerializer, BaseImportSerializer


def remove_prefill_from_variable(representation: FormVariableDataRepresentation):
    representation["prefill_plugin"] = ""
    representation["prefill_attribute"] = ""
    representation["prefill_options"] = {}


class FormVariableExportSerializer(
    FormVariableSerializer,
    BaseExportSerializer[FormVariable, FormVariableDataRepresentation],
):
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup[FormVariableDataRepresentation](
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

    def remove_sensitive_content(
        self, instance: FormVariable, representation: FormVariableDataRepresentation
    ) -> FormVariableDataRepresentation:
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


class FormVariableImportSerializer(
    FormVariableSerializer,
    BaseImportSerializer[FormVariable, FormVariableDataRepresentation],
):
    pass
