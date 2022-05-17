from typing import Any, Dict, Iterator

from .typing import Component


def iter_components(
    configuration: dict, recursive=True, _is_root=True, _mark_root=False
) -> Iterator[Component]:
    components = configuration.get("components")
    if configuration.get("type") == "columns" and recursive:
        assert not components, "Both nested components and columns found"
        for column in configuration["columns"]:
            yield from iter_components(
                configuration=column, recursive=recursive, _is_root=False
            )

    if components:
        for component in components:
            if _mark_root:
                component["_is_root"] = _is_root
            yield component
            if recursive:
                yield from iter_components(
                    configuration=component, recursive=recursive, _is_root=False
                )


def get_default_values(configuration: dict) -> Dict[str, Any]:
    defaults = {}

    for component in iter_components(configuration, recursive=True):
        if "key" not in component:
            continue
        if "defaultValue" not in component:
            continue
        defaults[component["key"]] = component["defaultValue"]

    return defaults
