from __future__ import annotations

import typing
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog
from glom import Coalesce, Path, glom
from opentelemetry import trace
from typing_extensions import TypeIs

from formio_types import (
    AnyComponent,
    Columns,
    EditGrid,
    Fieldset,
    FormioConfiguration as FormioConfigurationStruct,
)
from openforms.typing import JSONObject

from .typing import Column, ColumnsComponent, Component, FormioConfiguration

if TYPE_CHECKING:
    from .datastructures import FormioConfigurationWrapper, FormioData

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.formio.utils")

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


@tracer.start_as_current_span(
    name="iter-components",
    attributes={
        "span.type": "app",
        "span.subtype": "formio",
        "span.action": "configuration",
    },
)
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
                    if not recursive:
                        continue
                    if isinstance(component, EditGrid) and not recurse_into_editgrid:
                        continue
                    yield from iter_components(
                        component,
                        recursive=recursive,
                        recurse_into_editgrid=recurse_into_editgrid,
                    )
            case Columns(columns=columns):
                for column in columns:
                    for component in column.components:
                        yield component
                        if not recursive:
                            continue
                        if (
                            isinstance(component, EditGrid)
                            and not recurse_into_editgrid
                        ):
                            continue
                        yield from iter_components(
                            component,
                            recursive=recursive,
                            recurse_into_editgrid=recurse_into_editgrid,
                        )
            case EditGrid(components=editgrid_components):
                for component in editgrid_components:
                    yield component
                    if recursive:
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


@tracer.start_as_current_span(
    name="flatten-by-path",
    attributes={
        "span.type": "app",
        "span.subtype": "formio",
        "span.action": "configuration",
    },
)
def flatten_by_path(configuration: FormioConfiguration) -> dict[str, Component]:
    """
    Flatten the formio configuration.

    Takes a (nested) Formio configuration object and flattens it, using the full
    JSON path as key and the component as value in the returned mapping.
    """

    result = dict(iterate_components_with_configuration_path(configuration))
    return result


def get_readable_path_from_configuration_path(
    configuration: FormioConfiguration, path: str, prefix: str | None = ""
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


def is_visible_in_frontend(
    component: Component,
    data: FormioData,
    configuration_wrapper: FormioConfigurationWrapper,
) -> bool:
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

    assert conditional_show is not None

    # be resilient on the component key lookup - the old comparison seemed to mostly
    # work and this whole code should be cleaned up anyway when we go the msgspec route
    if trigger_component_key in configuration_wrapper:
        trigger_component = configuration_wrapper[trigger_component_key]
    else:
        trigger_component: Component = {
            "type": "unknown",
            "key": trigger_component_key,
            "label": "unknown",
        }
    trigger_component_value = data.get(trigger_component_key, None)
    compare_value = conditional.get("eq")

    # special treatment for emptyness check of file component - due to a bug in the
    # formio-builder you can configure the `eq` as an empty string by leaving it blank.
    # Our new renderer needed the same patch, and the legacy formio.js renderer already
    # exhibited this behaviour.
    if (
        trigger_component["type"] == "file"
        and compare_value == ""
        and trigger_component_value == []
    ):
        return conditional_show

    if (
        trigger_component["type"] == "selectboxes"
        and isinstance(trigger_component_value, dict)
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
