from typing import Any, Dict


def iter_components(configuration: dict, recursive=True) -> dict:
    components = configuration.get("components")
    if configuration.get("type") == "columns" and recursive:
        assert not components, "Both nested components and columns found"
        for column in configuration["columns"]:
            yield from iter_components(configuration=column, recursive=recursive)

    if components:
        for component in components:
            yield component
            if recursive:
                yield from iter_components(configuration=component, recursive=recursive)


def get_default_values(configuration: dict) -> Dict[str, Any]:
    defaults = {}

    for component in iter_components(configuration, recursive=True):
        if "key" not in component:
            continue
        if "defaultValue" not in component:
            continue
        defaults[component["key"]] = component["defaultValue"]

    return defaults
