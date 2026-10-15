from uuid import UUID

import tablib
from import_export.results import RowResult

from .datastructures import FormImportOptions
from .resources import ADDITIONAL_FORM_CONFIGURATION_RESOURCES


def import_additional_form_configuration_data(
    resources: dict[str, str],
    import_options: FormImportOptions,
    uuid_mapping: dict[str, str],
) -> None:
    resources_to_import = set(import_options.additional_form_configuration)
    unknown_options = resources_to_import - set(ADDITIONAL_FORM_CONFIGURATION_RESOURCES)

    if unknown_options:
        raise ValueError(
            f"Invalid additional form configuration option(s): {unknown_options}"
        )

    for option, (
        resource,
        output_name,
    ) in ADDITIONAL_FORM_CONFIGURATION_RESOURCES.items():
        # If the option is not in the import options, or there is no data to import,
        # skip it
        if option in resources_to_import and output_name in resources:
            # Run the import data through the resource
            dataset = tablib.Dataset().load(resources[output_name], "json")
            results = resource().import_data(dataset)

            # Add the import results to the uuid mapping
            for result in results:
                identifier_field: str = resource().identifier_field
                old_identifier: str = result.row_values.get(identifier_field)

                new_identifier: str | UUID | None = None

                match result.import_type:
                    case RowResult.IMPORT_TYPE_NEW:
                        new_identifier = getattr(result.instance, identifier_field)

                    case RowResult.IMPORT_TYPE_SKIP:
                        new_identifier = getattr(result.original, identifier_field)

                    case _:
                        # If the import results in anything other than new or skip, then
                        # something is going wrong
                        raise ValueError(f"Invalid import type: {result.import_type}")

                assert new_identifier is not None
                uuid_mapping[old_identifier] = str(new_identifier)
