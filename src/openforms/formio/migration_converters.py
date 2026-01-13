"""
Expose a centralized registry of migration converters.

This registry is used by the data migrations *and* form import. It guarantees that
component definitions are rewritten to be compatible with the current code.
"""

import json
from typing import Protocol, cast  # noqa: TID251

import structlog
from glom import assign, glom

from openforms.formio.constants import DataSrcOptions
from openforms.formio.typing.vanilla import ColumnsComponent, FileComponent
from openforms.typing import JSONObject

from .datastructures import FormioConfigurationWrapper
from .typing import AddressNLComponent, Component, MapComponent
from .utils import get_component_empty_value

logger = structlog.stdlib.get_logger(__name__)


class ComponentConverter(Protocol):
    def __call__(self, component: Component) -> bool:
        """
        Mutate a component in place.

        The component is guaranteed to have the 'expected' literal ``component["key"]``
        value because you bind it in ``CONVERTERS`` to this particular formio component
        type.

        :return: True if the component was modified, False if not, so that data
          migrations know whether a DB record needs to be updated or not.
        """
        ...


def move_time_validators(component: Component) -> bool:
    has_min_time = "minTime" in component
    has_max_time = "maxTime" in component
    if not (has_min_time or has_max_time):
        return False

    min_time = component.get("minTime")
    max_time = component.get("maxTime")

    component.setdefault("validate", {})
    if has_min_time:
        component["validate"]["minTime"] = min_time  # type: ignore
        del component["minTime"]

    if has_max_time:
        component["validate"]["maxTime"] = max_time  # type: ignore
        del component["maxTime"]

    return True


def alter_prefill_default_values(component: Component) -> bool:
    """A converter that replaces ``prefill`` dict values from ``None`` to an empty string."""
    if not (prefill := component.get("prefill") or {}):
        return False

    altered = False
    unset = object()

    prefill_plugin = prefill.get("plugin", unset)
    if prefill_plugin is None:
        component["prefill"]["plugin"] = ""
        altered = True

    prefill_attribute = prefill.get("attribute", unset)
    if prefill_attribute is None:
        component["prefill"]["attribute"] = ""
        altered = True

    return altered


def set_openforms_datasrc(component: Component) -> bool:
    # if a dataSrc is specified, there is nothing to do
    if glom(component, "openForms.dataSrc", default=None):
        return False
    assign(component, "openForms.dataSrc", val=DataSrcOptions.manual, missing=dict)
    return True


def fix_column_sizes(component: Component) -> bool:
    component = cast(ColumnsComponent, component)

    changed = False
    for column in component.get("columns", []):
        size = column.get("size", "6")
        size_mobile = column.get("sizeMobile")

        size_ok = isinstance(size, int)
        size_mobile_ok = size_mobile is None or isinstance(size_mobile, int)

        if size_ok and size_mobile_ok:
            continue

        changed = True
        if not size_ok:
            try:
                column["size"] = int(size)
            except (TypeError, ValueError):
                column["size"] = 6

        if not size_mobile_ok:
            try:
                column["sizeMobile"] = int(size_mobile)
            except (TypeError, ValueError):
                column["sizeMobile"] = 4

    return changed


def fix_file_default_value(component: Component) -> bool:
    component = cast(FileComponent, component)

    if "defaultValue" not in component:
        return False

    default_value = component["defaultValue"]
    empty_value = get_component_empty_value(component)

    match default_value:
        case list() if None in default_value:
            component["defaultValue"] = empty_value
            return True
        case None:
            component["defaultValue"] = empty_value
            return True
        case _:
            return False


def ensure_extra_zip_mimetypes_exist_in_file_type(component: Component) -> bool:
    component = cast(FileComponent, component)
    if not (file_type := glom(component, "file.type", default=None)) or not (
        file_pattern := component.get("filePattern", None)
    ):
        return False

    file_pattern_list = file_pattern.split(",")
    needed_mime_types = ("application/x-zip-compressed", "application/zip-compressed")

    def add_if_missing(current_list: list[str]):
        for item in needed_mime_types:
            if item not in current_list:
                current_list.append(item)

    if not ("application/zip" in file_type or "application/zip" in file_pattern_list):
        return False

    # file type
    add_if_missing(file_type)
    assign(component, "file.type", file_type)
    # file pattern
    add_if_missing(file_pattern_list)
    component["filePattern"] = ",".join(file_pattern_list)
    return True


def ensure_licensplate_validate_pattern(component: Component) -> bool:
    # assume that it's the correct pattern if it's set
    if "validate" in component and "pattern" in component["validate"]:
        return False

    component.setdefault("validate", {})
    component["validate"]["pattern"] = (
        r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"  # type: ignore
    )
    return True


def ensure_postcode_validate_pattern(component: Component) -> bool:
    # assume that it's the correct pattern if it's set
    if "validate" in component and "pattern" in component["validate"]:
        return False

    component.setdefault("validate", {})
    component["validate"]["pattern"] = (
        r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"  # type: ignore
    )
    return True


def prevent_datetime_components_from_emptying_invalid_values(
    component: Component,
) -> bool:
    # Issue #3755
    assign(component, "customOptions.allowInvalidPreload", True, missing=dict)
    return True


def fix_empty_validate_lengths(component: Component) -> bool:
    if not (validate := component.get("validate")):
        return False

    changed = False
    for key in ("minLength", "maxLength", "min", "max", "minWords", "maxWords"):
        if key in validate and validate[key] == "":  # type: ignore
            changed = True
            del validate[key]  # type: ignore

    return changed


def fix_multiple_empty_default_value(component: Component) -> bool:
    # GH-4084
    if not component.get("multiple", False):
        return False

    default_value = component.get("defaultValue")
    if default_value == [""]:
        component["defaultValue"] = []
        return True

    return False


def set_datatype_string(component: Component):
    # https://github.com/open-formulieren/open-forms/issues/4772
    if component.get("dataType") != "string":
        component["dataType"] = "string"
        return True
    return False


def convert_simple_conditionals(configuration: JSONObject) -> bool:
    config_modified = False

    config = FormioConfigurationWrapper(configuration)
    for component in config:
        if not (
            comparison_component_key := component.get("conditional", {}).get("when", "")
        ):
            continue

        assert "conditional" in component

        if comparison_component_key not in config:
            logger.warning(
                "component_not_found",
                key=comparison_component_key,
                configuration=configuration,
            )
            continue

        comparison_component = config[comparison_component_key]
        eq = component["conditional"].get("eq")
        if eq is None:
            continue

        if comparison_component["type"] in ["number", "currency"]:
            # only strings can be loaded
            if not isinstance(eq, str):
                continue
            component["conditional"]["eq"] = json.loads(eq)
            config_modified = True

        if comparison_component["type"] == "checkbox":
            if isinstance(eq, bool):
                continue

            component["conditional"]["eq"] = {
                "true": True,
                "false": False,
            }.get(eq, False)
            config_modified = True

    return config_modified


def remove_empty_conditional_values(component: Component) -> bool:
    config_modified = False

    if "conditional" not in component:
        return False

    conditional = component["conditional"]
    for known_key in ("eq", "when", "show"):
        if not (known_key in conditional and conditional[known_key] == ""):
            continue

        conditional.pop(known_key)
        config_modified = True

    return config_modified


def ensure_addressnl_has_deriveAddress(component: Component) -> bool:
    component = cast(AddressNLComponent, component)

    if "deriveAddress" in component:
        return False

    component.setdefault("deriveAddress", False)
    return True


def ensure_map_has_interactions(component: Component) -> bool:
    component = cast(MapComponent, component)

    if "interactions" in component:
        return False

    component.setdefault(
        "interactions",
        {
            "marker": True,
            "polygon": False,
            "polyline": False,
        },
    )
    return True


def rename_identifier_role_authorizee(component: Component) -> bool:
    if "prefill" not in component:
        return False
    if component["prefill"].get("identifierRole") != "authorised_person":
        return False
    component["prefill"]["identifierRole"] = "authorizee"
    return True


def fix_empty_default_value(component: Component) -> bool:
    if "defaultValue" not in component:
        return False

    changed = False
    if component["defaultValue"] is None:
        component["defaultValue"] = get_component_empty_value(component)
        changed = True

    if component.get("multiple", False):
        for index, value in enumerate(component["defaultValue"]):
            if value is None:
                component["defaultValue"][index] = ""
                changed = True

    return changed


def replace_empty_datepicker_properties(component: Component) -> bool:
    config_modified = False

    date_picker_config = component.get("datePicker", {})
    if "minDate" not in date_picker_config and "maxDate" not in date_picker_config:
        return False

    for property in ("minDate", "maxDate"):
        value = date_picker_config.get(property)

        if not (value == ""):
            continue

        date_picker_config[property] = None
        config_modified = True

    return config_modified


def empty_errors_property(component: Component) -> bool:
    if "errors" not in component:
        return False

    if len(component["errors"]) > 0:
        component["errors"] = {}
        return True

    return False


def remove_default_value_translation(component: Component) -> bool:
    config_modified = False

    translations = component.get("openForms", {}).get("translations", {})
    if not translations:
        return False

    for _, properties in translations.items():
        if "defaultValue" not in properties:
            continue

        properties.pop("defaultValue")
        config_modified = True

    return config_modified


def remove_unused_error_keys(component: Component) -> bool:
    config_modified = False

    error_translations = component.get("translatedErrors", {})
    if not error_translations:
        return False

    for _, properties in error_translations.items():
        for property in ("maxLength", "pattern"):
            if property not in properties:
                continue

            properties.pop(property)
            config_modified = True

    return config_modified


DEFINITION_CONVERTERS = [
    convert_simple_conditionals,
]


CONVERTERS: dict[str, dict[str, ComponentConverter]] = {
    # Input components
    "textfield": {
        "alter_prefill_default_values": alter_prefill_default_values,
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "rename_identifier_role_authorizee": rename_identifier_role_authorizee,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
        "remove_default_value_translation": remove_default_value_translation,
    },
    "email": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
        "remove_unused_error_keys": remove_unused_error_keys,
    },
    "date": {
        "alter_prefill_default_values": alter_prefill_default_values,
        "rename_identifier_role_authorizee": rename_identifier_role_authorizee,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "replace_empty_datepicker_properties": replace_empty_datepicker_properties,
    },
    "datetime": {
        "alter_prefill_default_values": alter_prefill_default_values,
        "prevent_datetime_components_from_emptying_invalid_values": prevent_datetime_components_from_emptying_invalid_values,
        "rename_identifier_role_authorizee": rename_identifier_role_authorizee,
        "replace_empty_datepicker_properties": replace_empty_datepicker_properties,
    },
    "time": {
        "move_time_validators": move_time_validators,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "phoneNumber": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
    },
    "postcode": {
        "alter_prefill_default_values": alter_prefill_default_values,
        "ensure_validate_pattern": ensure_postcode_validate_pattern,
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "rename_identifier_role_authorizee": rename_identifier_role_authorizee,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
    },
    "file": {
        "fix_default_value": fix_file_default_value,
        "ensure_extra_zip_mimetypes_exist_in_file_type": ensure_extra_zip_mimetypes_exist_in_file_type,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "textarea": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "map": {
        "ensure_map_has_interactions": ensure_map_has_interactions,
    },
    "number": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "select": {
        "set_openforms_datasrc": set_openforms_datasrc,
        "fix_multiple_empty_default_value": fix_multiple_empty_default_value,
        "set_datatype_string": set_datatype_string,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "remove_unused_error_keys": remove_unused_error_keys,
    },
    "selectboxes": {
        "set_openforms_datasrc": set_openforms_datasrc,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
    },
    "currency": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
    },
    "radio": {
        "set_openforms_datasrc": set_openforms_datasrc,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "remove_unused_error_keys": remove_unused_error_keys,
    },
    "checkbox": {
        "fix_empty_default_value": fix_empty_default_value,
        "remove_unused_error_keys": remove_unused_error_keys,
    },
    # Special components
    "iban": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "licenseplate": {
        "ensure_validate_pattern": ensure_licensplate_validate_pattern,
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
        "empty_errors_property": empty_errors_property,
    },
    "bsn": {
        "alter_prefill_default_values": alter_prefill_default_values,
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
        "rename_identifier_role_authorizee": rename_identifier_role_authorizee,
        "fix_empty_default_value": fix_empty_default_value,
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "cosign": {
        "fix_empty_validate_lengths": fix_empty_validate_lengths,
    },
    "addressNL": {
        "ensure_addressnl_has_deriveAddress": ensure_addressnl_has_deriveAddress
    },
    "editgrid": {
        "fix_empty_default_value": fix_empty_default_value,
    },
    "signature": {
        "fix_empty_default_value": fix_empty_default_value,
    },
    "content": {
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    "fieldset": {
        "remove_empty_conditional_values": remove_empty_conditional_values,
    },
    # Layout components
    "columns": {
        "fix_column_sizes": fix_column_sizes,
    },
}
"""A mapping of the component types to their converter functions.

Keys are ``component["type"]`` values, and values are dictionaries keyed by a
unique converter identifier and the function to do the actual conversion.
"""
