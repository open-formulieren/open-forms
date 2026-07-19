import structlog

from openforms.formio.migration_converters import CONVERTERS, DEFINITION_CONVERTERS
from openforms.formio.utils import iter_components
from openforms.forms.api.serializers import FormDefinitionSerializer
from openforms.forms.models import FormDefinition, Form
from openforms.import_export.typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
    FormImportOptions,
    ReusableFormDefinitionsOptions,
)
from openforms.prefill.constants import IdentifierRoles
from openforms.typing import JSONObject

from .base import BaseExportSerializer, BaseImportSerializer

logger = structlog.stdlib.get_logger(__name__)


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

    @staticmethod
    def resolve_instance(
        value: JSONObject,
        import_options: FormImportOptions | None,
        existing_form_instance: Form | None,
    ) -> FormDefinition | None:
        if import_options is None:
            return None

        match import_options.reusable_form_definitions:
            case ReusableFormDefinitionsOptions.create_new:
                return None

            case ReusableFormDefinitionsOptions.reuse_existing:
                return FormDefinition.objects.filter(
                    configuration=value.get("configuration"),
                    is_reusable=True,
                ).first()

            case _:
                raise RuntimeError(
                    f"Form definition import option {import_options.reusable_form_definitions} is not supported"
                )

    def to_internal_value(self, instance):
        value = instance.copy()

        if configuration := value.get("configuration"):
            self.apply_component_conversions(configuration)
            self.apply_definition_conversions(configuration)

        return super().to_internal_value(value)

    def apply_component_conversions(self, configuration: JSONObject):
        """
        Apply the known formio component conversions to the entire form definition.
        """
        log = logger.bind(action="forms.apply_component_conversions")
        for component in iter_components(configuration):
            if not (component_type := component.get("type")):  # pragma: no cover
                continue
            if not (converters := CONVERTERS.get(component_type)):
                continue
            for identifier, apply_converter in converters.items():
                log.debug(
                    "apply_converter",
                    component_type=component_type,
                    identifier=identifier,
                )
                apply_converter(component)

    def apply_definition_conversions(self, configuration: JSONObject):
        for converter in DEFINITION_CONVERTERS:
            converter(configuration)
