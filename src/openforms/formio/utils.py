from __future__ import annotations

import itertools
import typing
from collections.abc import Iterator, MutableMapping, Sequence
from typing import Any

import structlog
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
    recurse_into_editgrid: bool = True,
    parent_map: MutableMapping[str, str] | None = None,  # mapping from child to parent
    parent_key: str = "",
) -> Iterator[Component]: ...


@typing.overload
def iter_components(
    configuration: FormioConfigurationStruct | AnyComponent,
    *,
    recursive=True,
    recurse_into_editgrid: bool = True,
    parent_map: MutableMapping[str, str] | None = None,  # mapping from child to parent
    parent_key: str = "",
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
    recurse_into_editgrid: bool = True,
    parent_map: MutableMapping[str, str] | None = None,  # mapping from child to parent
    parent_key: str = "",
) -> Iterator[Component] | Iterator[AnyComponent]:
    _is_root = parent_key == ""
    if not isinstance(configuration, dict):
        match configuration:
            case FormioConfigurationStruct() | Fieldset():
                for component in configuration.components:
                    yield component
                    if parent_key and parent_map is not None:
                        parent_map[component.key] = parent_key
                    if not recursive:
                        continue
                    if isinstance(component, EditGrid) and not recurse_into_editgrid:
                        continue
                    yield from iter_components(
                        component,
                        recursive=recursive,
                        recurse_into_editgrid=recurse_into_editgrid,
                        parent_map=parent_map,
                        parent_key=getattr(configuration, "key", ""),
                    )
            case Columns(columns=columns):
                for column in columns:
                    for component in column.components:
                        yield component
                        if parent_key and parent_map is not None:
                            parent_map[component.key] = parent_key
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
                            parent_map=parent_map,
                            parent_key=configuration.key,
                        )
            case EditGrid(components=editgrid_components):
                for component in editgrid_components:
                    yield component
                    if parent_key and parent_map is not None:
                        parent_map[component.key] = parent_key
                    if recursive:
                        yield from iter_components(
                            component,
                            recursive=recursive,
                            recurse_into_editgrid=recurse_into_editgrid,
                            parent_map=parent_map,
                            parent_key=configuration.key,
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
                    recurse_into_editgrid=recurse_into_editgrid,
                    parent_map=parent_map,
                    parent_key=configuration["key"],
                )

        for component in components:
            yield component
            if parent_key and parent_map is not None:
                parent_map[component["key"]] = parent_key
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
                    recurse_into_editgrid=recurse_into_editgrid,
                    parent_map=parent_map,
                    parent_key=component["key"],
                )


def get_branch_representation(branch: Sequence[Component], *, prefix: str = "") -> str:
    """
    Get a readable version of a component tree branch.

    For example, for a branch ``[EditGridComponent, TextField]``, it returns
    ``Repeating group label > Textfield label``.
    """
    bits = itertools.chain(
        [prefix] if prefix else [],
        (node.get("label") or node["key"] for node in branch),
    )
    return " > ".join(bits)


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
