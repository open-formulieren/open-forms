import structlog

from openforms.formio.migration_converters import CONVERTERS, DEFINITION_CONVERTERS
from openforms.formio.typing import MapComponent
from openforms.formio.utils import iter_components
from openforms.typing import JSONObject

from ...api.serializers import FormDefinitionSerializer
from ...models import FormDefinition
from ..constants import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)
from ..datastructures import (
    AdditionalFormConfigurationCleanup,
    FormConfigurationCleanup,
)
from ..typing import (
    FormDefinitionDataRepresentation,
)
from .base import BaseExportSerializer, BaseImportSerializer

logger = structlog.stdlib.get_logger(__name__)


def clear_wms_tile_layers(representation: FormDefinitionDataRepresentation):
    from typing import cast  # noqa: TID251

    for component in iter_components(representation.get("configuration", {})):
        if component["type"] != "map":
            continue

        # Casting for type-safety, we know that the component is a map component
        component = cast(MapComponent, component)
        for overlay in component.get("overlays", []):
            overlay["uuid"] = ""
            overlay["layers"] = []


def clear_wmts_tile_layers(representation: FormDefinitionDataRepresentation):
    from typing import cast  # noqa: TID251

    for component in iter_components(representation.get("configuration", {})):
        if component["type"] != "map" or "tileLayerIdentifier" not in component:
            continue

        # Casting for type-safety, we know that the component is a map component
        component = cast(MapComponent, component)
        component["tileLayerIdentifier"] = ""


def remove_prefill_from_component_configuration(
    representation: FormDefinitionDataRepresentation,
):
    for component in iter_components(representation.get("configuration", {})):
        if "prefill" not in component:
            return
        component["prefill"]["plugin"] = ""
        component["prefill"]["attribute"] = ""


class FormDefinitionExportSerializer(
    FormDefinitionSerializer,
    BaseExportSerializer[FormDefinition, FormDefinitionDataRepresentation],
):
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup[FormDefinitionDataRepresentation](
            option=AdditionalFormConfigurationOptions.wms_tile_layers,
            cleanup=clear_wms_tile_layers,
        ),
        AdditionalFormConfigurationCleanup[FormDefinitionDataRepresentation](
            option=AdditionalFormConfigurationOptions.wmts_tile_layers,
            cleanup=clear_wmts_tile_layers,
        ),
    )
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup[FormDefinitionDataRepresentation](
            option=FormConfigurationOptions.prefill,
            cleanup=remove_prefill_from_component_configuration,
        ),
    )
    safe_export_fields = (
        "url",
        "uuid",
        "name",
        "internal_name",
        "slug",
        "configuration",
        "login_required",
        "is_reusable",
        "translations",
    )

    def remove_sensitive_content(
        self,
        instance: FormDefinition,
        representation: FormDefinitionDataRepresentation,
    ) -> FormDefinitionDataRepresentation:
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


class FormDefinitionImportSerializer(
    FormDefinitionSerializer, BaseImportSerializer[FormDefinitionDataRepresentation]
):
    def prepare_for_import(
        self, instance: FormDefinitionDataRepresentation
    ) -> FormDefinitionDataRepresentation:
        if configuration := instance.get("configuration"):
            self.apply_component_conversions(configuration)
            self.apply_definition_conversions(configuration)

        return instance

    @staticmethod
    def apply_component_conversions(configuration: JSONObject) -> None:
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

    @staticmethod
    def apply_definition_conversions(configuration: JSONObject) -> None:
        for converter in DEFINITION_CONVERTERS:
            converter(configuration)
