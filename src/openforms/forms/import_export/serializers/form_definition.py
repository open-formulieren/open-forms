from openforms.formio.typing import MapComponent
from openforms.formio.utils import iter_components

from ...api.serializers import FormDefinitionSerializer
from ...models import FormDefinition
from ..typing import (
    AdditionalFormConfigurationCleanup,
    AdditionalFormConfigurationOptions,
    FormConfigurationCleanup,
    FormConfigurationOptions,
    FormDefinitionExportRepresentation,
)
from .base import BaseExportSerializer


def clear_wms_tile_layers(representation: FormDefinitionExportRepresentation):
    from typing import cast  # noqa: TID251

    for component in iter_components(representation.get("configuration", {})):
        if component["type"] != "map":
            continue

        # Casting for type-safety, we know that the component is a map component
        component = cast(MapComponent, component)
        for overlay in component.get("overlays", []):
            overlay["uuid"] = ""
            overlay["layers"] = []


def clear_wmts_tile_layers(representation: FormDefinitionExportRepresentation):
    from typing import cast  # noqa: TID251

    for component in iter_components(representation.get("configuration", {})):
        if component["type"] != "map" or "tileLayerIdentifier" not in component:
            continue

        # Casting for type-safety, we know that the component is a map component
        component = cast(MapComponent, component)
        component["tileLayerIdentifier"] = ""


def remove_prefill_from_component_configuration(
    representation: FormDefinitionExportRepresentation,
):
    for component in iter_components(representation.get("configuration", {})):
        if "prefill" not in component:
            return
        component["prefill"]["plugin"] = ""
        component["prefill"]["attribute"] = ""


class FormDefinitionExportSerializer(
    FormDefinitionSerializer,
    BaseExportSerializer[FormDefinition, FormDefinitionExportRepresentation],
):
    excluded_additional_form_configuration_cleanup = (
        AdditionalFormConfigurationCleanup[FormDefinitionExportRepresentation](
            option=AdditionalFormConfigurationOptions.wms_tile_layers,
            cleanup=clear_wms_tile_layers,
        ),
        AdditionalFormConfigurationCleanup[FormDefinitionExportRepresentation](
            option=AdditionalFormConfigurationOptions.wmts_tile_layers,
            cleanup=clear_wmts_tile_layers,
        ),
    )
    excluded_form_configuration_cleanup = (
        FormConfigurationCleanup[FormDefinitionExportRepresentation](
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
        representation: FormDefinitionExportRepresentation,
    ) -> FormDefinitionExportRepresentation:
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
