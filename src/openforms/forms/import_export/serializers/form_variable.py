from ...api.serializers import FormVariableSerializer
from ...models import FormVariable
from ..constants import FormConfigurationOptions
from ..datastructures import FormConfigurationCleanup
from ..typing import FormVariableData
from .base import BaseExportSerializer, BaseImportSerializer


def remove_prefill_from_variable(data: FormVariableData):
    """
    Remove prefill data from the variable.

    :param data: FormVariableData The Form variable data as dict. This could be either
    the representation of data to be exported or data to be imported.
    """
    data["prefill_plugin"] = ""
    data["prefill_attribute"] = ""
    data["prefill_options"] = {}


class FormVariableExportSerializer(
    FormVariableSerializer,
    BaseExportSerializer[FormVariable, FormVariableData],
):
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup[FormVariableData](
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
        self, instance: FormVariable, representation: FormVariableData
    ) -> FormVariableData:
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
    FormVariableSerializer, BaseImportSerializer[FormVariable, FormVariableData]
):
    excluded_form_configuration_removal = (
        FormConfigurationCleanup[FormVariableData](
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_variable,
        ),
    )

    def prepare_for_import(self, instance: FormVariableData) -> FormVariableData:
        if "service_fetch_configuration" in instance:
            # The transferring between systems case is very tricky better not import
            # these, we don't know where this came from. Services and ids may point to
            # different things in different OF instances. Even when restoring a form
            # version, we don't know if the service is the same as it was before.
            del instance["service_fetch_configuration"]

        return instance
