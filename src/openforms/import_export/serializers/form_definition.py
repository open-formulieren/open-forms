from openforms.formio.utils import iter_components
from openforms.forms.api.serializers import FormDefinitionSerializer
from openforms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.typing import JSONObject

from .base import BaseExportSerializer, BaseImportSerializer


def clear_wms_tile_layers(representation: JSONObject):
    for component in representation.get("configuration", {}).get("components", []):
        if component["type"] != "map":
            continue

        for overlay in component.get("overlays", []):
            overlay["uuid"] = ""
            overlay["layers"] = []


def clear_wmts_tile_layers(representation: JSONObject):
    for component in representation.get("configuration", {}).get("components", []):
        if component["type"] != "map" or "tileLayerIdentifier" not in component:
            continue

        component["tileLayerIdentifier"] = ""


def remove_prefill_from_component_configuration(representation: JSONObject):
    for component in representation.get("configuration", {}).get("components", []):
        if "prefill" not in component:
            return
        component["prefill"]["plugin"] = ""
        component["prefill"]["attribute"] = ""
        component["prefill"]["identifier_role"] = IdentifierRoles.main


class FormDefinitionExportSerializer(FormDefinitionSerializer, BaseExportSerializer):
    is_exporting = True
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.wms_tile_layers,
            cleanup=clear_wms_tile_layers,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.wmts_tile_layers,
            cleanup=clear_wmts_tile_layers,
        ),
    )
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


class FormDefinitionImportSerializer(FormDefinitionSerializer, BaseImportSerializer):
    excluded_additional_form_configuration_removal = (
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.wms_tile_layers,
            cleanup=clear_wms_tile_layers,
        ),
        AdditionalFormConfigurationCleanup(
            option=AdditionalFormConfigurationOptions.wmts_tile_layers,
            cleanup=clear_wmts_tile_layers,
        ),
    )
    excluded_form_configuration_removal = (
        FormConfigurationCleanup(
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_component_configuration,
        ),
    )
