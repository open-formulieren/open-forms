"""
Map formio types to python types.

This is a temporary module to sort out the component type mapping from formio -> python,
so that django-camunda can map it to the appropriate Camunda type information.

The work in #1068 should eventually make this module obsolete.
"""
from typing import Any, Dict, List, Union

from dateutil import parser


def to_str(c, value) -> str:
    return str(value)


def number(c, value) -> Union[float, int, str]:
    if isinstance(value, (int, float)):
        return value

    try:
        return int(value)
    except ValueError:
        pass

    return str(value)


def select(component, value) -> str:
    if not (appointment_config := component.get("appointments")):
        return str(value)

    if appointment_config.get("showDates"):
        return TYPE_MAP["date"](component, value)

    if appointment_config.get("showTimes"):
        return parser.parse(value)

    return str(value)


def selectboxes(component, value) -> List[str]:
    return [key for key, checked in value.items() if checked]


# See src/openforms/js/formio_module.js for the available types
TYPE_MAP = {
    None: lambda c, v: None,
    "textarea": to_str,
    "textfield": to_str,
    "iban": to_str,
    "date": lambda c, value: parser.parse(value).date(),
    "signature": to_str,  # TODO: file like obj?
    "time": lambda c, value: parser.parse(value).time(),
    "number": number,
    "phoneNumber": to_str,
    "bsn": to_str,
    "postcode": to_str,
    "file": lambda c, value: value,  # TODO: file like, dict that needs formatting?
    "select": select,
    "radio": to_str,
    "selectboxes": selectboxes,
    "email": to_str,
    "map": lambda c, value: value,  # list of coordinates (lng, lat) in float format
    "password": to_str,
    "licenseplate": to_str,
}


def to_python(component: Dict[str, Any], value: Any) -> Any:
    converter = TYPE_MAP.get(component["type"], to_str)

    multiple = component.get("multiple", False)
    if multiple:
        return [converter(component, x) for x in value]
    else:
        return converter(component, value)
