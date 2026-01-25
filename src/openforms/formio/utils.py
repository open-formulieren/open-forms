from __future__ import annotations

import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import elasticapm
import structlog
from glom import Coalesce, Path, glom
from typing_extensions import TypeIs

from formio_types import (
    AnyComponent,
    Columns,
    Content,
    EditGrid,
    Fieldset,
    FormioConfiguration as FormioConfigurationStruct,
    SoftRequiredErrors,
)
from openforms.typing import JSONObject, JSONValue
from openforms.variables.constants import DEFAULT_INITIAL_VALUE, FormVariableDataTypes

from .constants import COMPONENT_DATA_SUBTYPES, COMPONENT_DATATYPES
from .typing import Column, ColumnsComponent, Component, FormioConfiguration

if TYPE_CHECKING:
    from .datastructures import FormioData

logger = structlog.stdlib.get_logger(__name__)

# XXX: we should probably be able to narrow this in Python 3.11 with non-total typed
# dicts.
type ComponentLike = (
    FormioConfiguration | JSONObject | Component | ColumnsComponent | Column
)


def _is_column_component(component: ComponentLike) -> TypeIs[ColumnsComponent]:
    return component.get("type") == "columns"


@typing.overload
def iter_components(
    configuration: ComponentLike,
    *,
    recursive=True,
    _is_root=True,
    _mark_root=False,
    recurse_into_editgrid: bool = True,
) -> Iterator[Component]: ...


@typing.overload
def iter_components(
    configuration: FormioConfigurationStruct | AnyComponent,
    *,
    recursive=True,
    recurse_into_editgrid: bool = True,
) -> Iterator[AnyComponent]: ...


@elasticapm.capture_span(span_type="app.formio.configuration")
def iter_components(
    configuration: ComponentLike | FormioConfigurationStruct | AnyComponent,
    *,
    recursive=True,
    _is_root=True,
    _mark_root=False,
    recurse_into_editgrid: bool = True,
) -> Iterator[Component] | Iterator[AnyComponent]:
    if not isinstance(configuration, dict):
        match configuration:
            case FormioConfigurationStruct() | Fieldset():
                for component in configuration.components:
                    yield component
                    if recursive:
                        yield from iter_components(
                            component,
                            recursive=recursive,
                            recurse_into_editgrid=recurse_into_editgrid,
                        )
            case Columns(columns=columns) if recursive:
                for column in columns:
                    for component in column.components:
                        yield from iter_components(
                            component,
                            recursive=recursive,
                            recurse_into_editgrid=recurse_into_editgrid,
                        )
            case EditGrid(components=editgrid_components) if (
                recursive and recurse_into_editgrid
            ):
                for component in editgrid_components:
                    yield from iter_components(
                        component,
                        recursive=recursive,
                        recurse_into_editgrid=recurse_into_editgrid,
                    )
            case _:
                pass
    else:
        components = configuration.get("components", [])
        assert isinstance(components, list)
        if _is_column_component(configuration) and recursive:
            assert not components, "Both nested components and columns found"
            for column in configuration["columns"]:
                yield from iter_components(
                    configuration=column,
                    recursive=recursive,
                    _is_root=False,
                    recurse_into_editgrid=recurse_into_editgrid,
                )

        for component in components:
            if _mark_root:
                component["_is_root"] = _is_root
            yield component
            if recursive:
                # TODO: find a cleaner solution - currently just not yielding these is not
                # an option because we have some special treatment for editgrid data which
                # 'copies' the nested components for further processing.
                # Ideally, with should be able to delegate this behaviour to the registered
                # component classes, but that's a refactor too big for the current task(s).
                if component.get("type") == "editgrid" and not recurse_into_editgrid:
                    continue
                yield from iter_components(
                    configuration=component,
                    recursive=recursive,
                    _is_root=False,
                    recurse_into_editgrid=recurse_into_editgrid,
                )


def iterate_components_with_configuration_path(
    configuration: ComponentLike, prefix: str = "components", recursive=True
) -> Iterator[tuple[str, Component]]:
    for index, component in enumerate(iter_components(configuration, recursive=False)):
        full_path = f"{prefix}.{index}"
        yield full_path, component

        # could be a component, could be something else
        has_components = "components" in component
        has_columns = "columns" in component

        if has_columns and recursive:
            for col_index, column in enumerate(component["columns"]):
                nested_prefix = f"{full_path}.columns.{col_index}.components"
                yield from iterate_components_with_configuration_path(
                    column, prefix=nested_prefix
                )
        elif has_components and recursive:
            yield from iterate_components_with_configuration_path(
                component, prefix=f"{full_path}.components"
            )


@elasticapm.capture_span(span_type="app.formio.configuration")
def flatten_by_path(configuration: JSONObject) -> dict[str, Component]:
    """
    Flatten the formio configuration.

    Takes a (nested) Formio configuration object and flattens it, using the full
    JSON path as key and the component as value in the returned mapping.
    """

    result = dict(iterate_components_with_configuration_path(configuration))
    return result


def get_readable_path_from_configuration_path(
    configuration: JSONObject, path: str, prefix: str | None = ""
) -> str:
    """
    Get a readable version of the configuration path.

    For example, for a path ``components.0.components.1`` and a configuration:

        .. code:: json

            {
              "components": [
                {
                  "key": "repeatingGroup",
                  "label": "Repeating Group",
                  "components": [
                    {
                      "key": "item1",
                      "label": "Item 1",
                    },
                    {
                      "key": "item2"
                      "label": "Item 2",
                    }
                  ]
                }
              ]
            }

    it returns ``Repeating Group > Item 1``.
    """
    keys_path = []
    if prefix:
        keys_path.append(prefix)

    previous_path_bit = Path()
    for path_bit in Path.from_text(path).values():
        label_or_key = glom(
            configuration,
            Coalesce(
                Path(previous_path_bit, path_bit, "label"),
                Path(previous_path_bit, path_bit, "key"),
            ),
            default=None,
        )

        if label_or_key:
            keys_path.append(label_or_key)

        previous_path_bit = Path(previous_path_bit, path_bit)

    return " > ".join(keys_path)


def is_layout_component(component: Component | AnyComponent) -> bool:
    # msgspec struct
    if not isinstance(component, dict):
        # TODO: define classvar property on component class itself?
        match component:
            case Content() | Columns() | Fieldset() | SoftRequiredErrors():
                return True
            case _:
                return False

    # Adapted from isLayoutComponent util function in Formio
    # https://github.com/formio/formio.js/blob/4.13.x/src/utils/formUtils.js#L25
    # FIXME ideally there would be a cleaner fix for this
    if component["type"] == "editgrid":
        return False

    column = component.get("columns")
    components = component.get("components")
    rows = component.get("rows")

    if (
        (column and isinstance(column, list))
        or (components and isinstance(components, list))
        or (rows and isinstance(rows, list))
    ):
        return True

    return False


def get_component_datatype(component: Component):
    component_type = component["type"]
    if component.get("multiple"):
        return FormVariableDataTypes.array
    return COMPONENT_DATATYPES.get(component_type, FormVariableDataTypes.string)


def get_component_data_subtype(component: Component) -> str:
    """
    Get the data subtype of a component.

    :returns: The original data type of the component if the component is configured as
      'multiple', an empty string otherwise. Components that are already an array
      (editgrid, files, partners, children and profile) are a special case, as 'multiple'
      is not relevant for these.
    """
    if subtype := COMPONENT_DATA_SUBTYPES.get(component["type"], None):
        return subtype

    if not component.get("multiple"):
        return ""

    return COMPONENT_DATATYPES.get(component["type"], FormVariableDataTypes.string)


def get_component_empty_value(component: Component):
    data_type = get_component_datatype(component)

    if component["type"] == "selectboxes":
        # Issue 2838
        # Component selectboxes is of 'object' type, which would return a {} for an
        # empty component. However, the empty value is with all the options not selected
        # (ex. {"a": False, "b": False})
        # Additionally, the `defaultValue` will be empty if the component uses another
        # variable or reference lists as a data source. We can generate a correct empty
        # value from the `values` if the formio configuration was updated dynamically.
        if not (empty_value := component.get("defaultValue", {})):
            values = component.get("values", {})
            if not (len(values) == 1 and values[0]["label"] == ""):
                empty_value = {item["label"]: False for item in values}
        return empty_value

    if component["type"] == "map":
        # Issue 5151
        # Component map is of 'object' type, which would return a {} for an empty component.
        # However, an empty object would fail validation, as the required properties
        # `type` and `coordinates` would be missing.
        return component.get("defaultValue", None)

    return DEFAULT_INITIAL_VALUE.get(data_type, "")


def get_component_default_value(component: Component) -> Any | None:
    # Formio has a getter for the:
    # - emptyValue: https://github.com/formio/formio.js/blob/4.13.x/src/components/textfield/TextField.js#L58
    # - defaultValue:
    #    https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/Component.js#L2302
    # If the defaultValue is empty, then the field will be populated with the emptyValue in the form data.
    default_value = component.get("defaultValue")
    if component.get("multiple") and default_value is None:
        return []
    return default_value


def is_visible_in_frontend(component: Component, data: FormioData) -> bool:
    """Check if the component is visible because of frontend logic

    The rules in formio are expressed as:

    .. code-block:: json

        {
            "show": true/false,
            "when": <key of trigger component>,
            "eq": <compare value>
        }

    .. warning:: this function currently does not take parent components into account
       that may be hidden, which lead to this component being hidden too.
    """
    hidden = component.get("hidden")
    conditional = component.get("conditional")

    if not conditional or (conditional_show := conditional.get("show")) in [None, ""]:
        return not hidden

    if not (trigger_component_key := conditional.get("when")):
        return not hidden

    trigger_component_value = data.get(trigger_component_key, None)
    compare_value = conditional.get("eq")

    if (
        isinstance(trigger_component_value, dict)
        and compare_value in trigger_component_value
    ):
        return (
            conditional_show
            if trigger_component_value[compare_value]
            else not conditional_show
        )

    return (
        conditional_show
        if trigger_component_value == compare_value
        else not conditional_show
    )


@dataclass
class ComponentWithDataItem:
    component: JSONObject
    upload_info: JSONObject
    data_path: str
    configuration_path: str


def iterate_data_with_components(
    configuration: JSONObject,
    data: FormioData,
    data_path: str = "",
    configuration_path: str = "components",
    filter_types: list[str] = None,
) -> Iterator[ComponentWithDataItem] | None:
    """
    Iterate through a configuration and return a tuple with the component JSON, its value in the submission data
    and the path within the submission data.

    For example, for a configuration with components:

    .. code:: json

        [
            {"key": "surname", "type": "textfield"},
            {"key": "pets", "type": "editgrid", "components": [{"key": "name", "type": "textfield"}]}
        ]

    And a submission data:

    .. code:: json

        {"surname": "Doe", "pets": [{"name": "Qui"}, {"name": "Quo"}, {"name": "Qua"}] }

    For the "Qui" item of the repeating group this function would yield:
    ``ComponentWithDataItem({"key": "name", "type": "textfield"}, "Qui", "pets", "pets.0.name")``.
    """
    if configuration.get("type") == "columns":
        for index, column in enumerate(configuration["columns"]):
            child_configuration_path = f"{configuration_path}.columns.{index}"
            yield from iterate_data_with_components(  # type: ignore
                column, data, data_path, child_configuration_path, filter_types
            )

    parent_type = configuration.get("type")
    if parent_type == "editgrid":
        parent_path = (
            f"{data_path}.{configuration['key']}" if data_path else configuration["key"]
        )
        group_data = data.get(parent_path, [])
        for index in range(len(group_data)):
            yield from iterate_data_with_components(  # type: ignore
                {"components": configuration.get("components", [])},
                data,
                data_path=f"{parent_path}.{index}",
                configuration_path=f"{configuration_path}.components",
                filter_types=filter_types,
            )
    else:
        base_configuration_path = configuration_path
        if parent_type == "fieldset":
            base_configuration_path += ".components"
        for index, child_component in enumerate(configuration.get("components", [])):
            child_configuration_path = f"{base_configuration_path}.{index}"
            yield from iterate_data_with_components(  # type: ignore
                child_component, data, data_path, child_configuration_path, filter_types
            )

    filter_out = (parent_type not in filter_types) if filter_types else False
    if "key" in configuration and not filter_out:
        component_data_path = (
            f"{data_path}.{configuration['key']}" if data_path else configuration["key"]
        )
        component_data = data.get(component_data_path)
        if component_data is not None:
            yield ComponentWithDataItem(  # type: ignore
                configuration,
                component_data,
                component_data_path,
                configuration_path,
            )


def recursive_apply(
    input: JSONValue, func: Callable, transform_leaf: bool = False, *args, **kwargs
):
    """
    Take an input - property value and recursively apply ``func`` to it.

    The ``input`` may be a string to be used as template, another JSON primitive
    that we can't pass through the template engine or a complex JSON object to
    recursively render.

    Returns the same datatype as the input datatype, which should be ready for
    JSON serialization unless transform_leaf flag is set to True where func is
    applied to the nested value as well.
    """
    match input:
        # string primitive - we can throw it into the template engine
        case str():
            return func(input, *args, **kwargs)

        # collection - map every item recursively
        case list():
            return [
                recursive_apply(nested_bit, func, transform_leaf, *args, **kwargs)
                for nested_bit in input
            ]

        # mapping - map every key/value pair recursively
        case dict():
            return {
                key: recursive_apply(nested_bit, func, transform_leaf, *args, **kwargs)
                for key, nested_bit in input.items()
            }

        case _:
            # other primitive or complex object - we can't template this out, so return it
            # unmodified unless the transformation is explicitly requested
            return func(input, *args, **kwargs) if transform_leaf else input
