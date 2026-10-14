from collections.abc import Mapping
from uuid import UUID

import tablib
from import_export.results import RowResult

from .datastructures import FormImportOptions
from .resources import ADDITIONAL_FORM_CONFIGURATION_RESOURCES
from .uuid_map import UUIDMap


def import_additional_form_configuration_data(
    resources: Mapping[str, str],
    import_options: FormImportOptions,
    uuid_mapping: UUIDMap,
) -> None:
    """
    Import additional form configuration data from the given resources.

    :param resources: A mapping of resource names to their JSON data.
    :param import_options: The import options, specifying which additional form
        configuration data to import.
    :param uuid_mapping: The UUID mapping to update with the imported data.
    """
    resources_to_import = set(import_options.additional_form_configuration)

    for option in resources_to_import:
        resource, output_name = ADDITIONAL_FORM_CONFIGURATION_RESOURCES[option]
        if output_name not in resources:
            # If the output name is not in the resources, then we cannot import it.
            continue

        # Run the import data through the resource
        dataset = tablib.Dataset().load(resources[output_name], "json")
        results = resource().import_data(dataset)

        # Add the import results to the uuid mapping
        for result in results:
            identifier_field: str = resource().identifier_field
            # If the old identifier is not present, then something is wrong with the
            # import data
            old_identifier: str | None = result.row_values.get(identifier_field)
            assert old_identifier is not None

            new_identifier: str | UUID | None = None
            match result.import_type:
                case RowResult.IMPORT_TYPE_NEW:
                    new_identifier = getattr(result.instance, identifier_field)

                case RowResult.IMPORT_TYPE_SKIP:
                    new_identifier = getattr(result.original, identifier_field)

                case _:  # pragma: no cover
                    # If the import results in anything other than new or skip, then
                    # something is going wrong
                    raise ValueError(f"Invalid import type: {result.import_type}")

            assert new_identifier is not None
            assert isinstance(new_identifier, (str, UUID))
            uuid_mapping.add(old_identifier, new_identifier)
