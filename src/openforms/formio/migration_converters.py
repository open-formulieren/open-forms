"""
Expose a centralized registry of migration converters.

This registry is used by the data migrations *and* form import. It guarantees that
component definitions are rewritten to be compatible with the current code.
"""
from typing import Protocol, cast

from glom import assign, glom

from openforms.formio.typing.vanilla import ColumnsComponent, FileComponent

from .typing import Component


class ComponentConverter(Protocol):
    def __call__(self, component: Component) -> bool:  # pragma: no cover
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
    assign(component, "openForms.dataSrc", val="manual", missing=dict)
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
    default_value = component.get("defaultValue")

    match default_value:
        case list() if None in default_value:
            component["defaultValue"] = None
            return True
        case _:
            return False


CONVERTERS: dict[str, dict[str, ComponentConverter]] = {
    # Input components
    "textfield": {
        "alter_prefill_default_values": alter_prefill_default_values,
    },
    "date": {
        "alter_prefill_default_values": alter_prefill_default_values,
    },
    "datetime": {
        "alter_prefill_default_values": alter_prefill_default_values,
    },
    "time": {
        "move_time_validators": move_time_validators,
    },
    "select": {"set_openforms_datasrc": set_openforms_datasrc},
    "selectboxes": {"set_openforms_datasrc": set_openforms_datasrc},
    "radio": {"set_openforms_datasrc": set_openforms_datasrc},
    "postcode": {
        "alter_prefill_default_values": alter_prefill_default_values,
    },
    "file": {
        "fix_default_value": fix_file_default_value,
    },
    # Special components
    "bsn": {
        "alter_prefill_default_values": alter_prefill_default_values,
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
