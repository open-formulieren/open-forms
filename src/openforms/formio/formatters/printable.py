non_printable_component_types = [
    "button",
    "htmlelement",
    "content",
    "columns",
    "fieldset",
    "panel",
    "tabs",
    "well",
]


def is_printable(component):
    # for safety, we assume every component type to be printable unless blacklisted
    try:
        return component["type"] not in non_printable_component_types
    except KeyError:
        return False


def filter_printable(components):
    return filter(is_printable, components)
