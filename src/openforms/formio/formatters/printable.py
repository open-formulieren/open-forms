from typing import Iterable

NON_PRINTABLE_COMPONENT_TYPES = [
    "button",
    "htmlelement",
    "content",
    "columns",
    "fieldset",
    "panel",
    "tabs",
    "well",
]


def is_printable(component: dict) -> bool:
    # for safety, we assume every component type to be printable unless blacklisted
    try:
        return component["type"] not in NON_PRINTABLE_COMPONENT_TYPES
    except KeyError:
        return False


def filter_printable(components: Iterable[dict]) -> Iterable[dict]:
    return filter(is_printable, components)
