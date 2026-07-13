from dataclasses import dataclass

import tablib
from import_export.results import RowResult

from openforms.forms.models import Form
from openforms.typing import JSONObject

from .resources import (
    BaseResource,
    ProductResource,
    WMSTileLayerResource,
    WMTSTileLayerResource,
    YiviAttributeGroupResource,
)
from .typing import (
    AdditionalFormConfigurationOptions,
    FormExportOptions,
    FormImportOptions,
)


@dataclass(frozen=True)
class ResourceConfig:
    resource: type[BaseResource]
    output_name: str


ADDITIONAL_FORM_CONFIGURATION_RESOURCES: dict[
    AdditionalFormConfigurationOptions,
    ResourceConfig,
] = {
    AdditionalFormConfigurationOptions.product: ResourceConfig(
        resource=ProductResource,
        output_name="product",
    ),
    AdditionalFormConfigurationOptions.wms_tile_layers: ResourceConfig(
        resource=WMSTileLayerResource,
        output_name="wmsTileLayers",
    ),
    AdditionalFormConfigurationOptions.wmts_tile_layers: ResourceConfig(
        resource=WMTSTileLayerResource,
        output_name="wmtsTileLayers",
    ),
    AdditionalFormConfigurationOptions.yivi_attribute_groups: ResourceConfig(
        resource=YiviAttributeGroupResource,
        output_name="yiviAttributeGroups",
    ),
}


def get_additional_form_configuration_data(
    form: Form, export_options: FormExportOptions
) -> JSONObject:
    """
    Create a dictionary of additional form configuration data for the given form.

    The keys are the names for the export files, and the values are the JSON data
    representing the resource data. This should be used in the form export process, in
    connection with `remove_excluded_additional_configuration_from_form`.
    """
    resources = {}

    selected_options = set(export_options.additional_form_configuration)
    unknown_options = selected_options - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, config in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        if option in selected_options:
            resources[config.output_name] = config.resource().export_for_form(form).json

    return resources


def import_additional_form_configuration_data(
    resources: JSONObject,
    import_options: FormImportOptions,
    uuid_mapping=dict[str, str],
):
    selected_options = set(import_options.additional_form_configuration)
    unknown_options = selected_options - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, config in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        if option in selected_options and config.output_name in resources:
            dataset = tablib.Dataset().load(resources[config.output_name], "json")
            results = config.resource().import_data(dataset)

            for row_result in results:
                identifier_field = config.resource.identifier_field
                old_identifier = row_result.row_values.get(identifier_field)

                new_identifier = None
                match row_result.import_type:
                    case RowResult.IMPORT_TYPE_NEW:
                        new_identifier = getattr(row_result.instance, identifier_field)

                    case RowResult.IMPORT_TYPE_SKIP:
                        new_identifier = getattr(row_result.original, identifier_field)

                    case _:
                        raise ValueError(
                            f"Invalid import type: {row_result.import_type}"
                        )

                if new_identifier is not None:
                    uuid_mapping[old_identifier] = str(new_identifier)
