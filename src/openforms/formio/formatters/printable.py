from typing import Iterable

from ..typing import Component

NON_PRINTABLE_COMPONENT_TYPES = [
    "button",
    "htmlelement",
    # "content",
    # "columns",
    # "fieldset",
    "panel",
    "tabs",
    "well",
]


def is_printable(component: Component) -> bool:
    # for safety, we assume every component type to be printable unless blacklisted
    try:
        return component["type"] not in NON_PRINTABLE_COMPONENT_TYPES
    except KeyError:
        return False


def is_printable_blacklisted(component: Component) -> bool:
    return component["type"] in NON_PRINTABLE_COMPONENT_TYPES


def filter_printable(components: Iterable[Component]) -> Iterable[Component]:
    return filter(is_printable, components)
