"""
Map formio types to python types.

This is a temporary module to sort out the component type mapping from formio -> python,
so that django-camunda can map it to the appropriate Camunda type information.

The work in #1068 should eventually make this module obsolete.
"""
from decimal import Decimal
from typing import Any, Dict, List

from dateutil import parser


def to_str(c, value) -> str:
    return str(value)


def noop(c, value: Any) -> Any:
    return value


def select(component, value) -> str:
    if not (appointment_config := component.get("appointments")):
        return str(value)

    if appointment_config.get("showDates"):
        return TYPE_MAP["date"](component, value)

    if appointment_config.get("showTimes"):
        return parser.parse(value)

    if isinstance(value, dict):
        return value

    return str(value)


def selectboxes(component, value) -> List[str]:
    return [key for key, checked in value.items() if checked]


# See src/openforms/js/formio_module.js for the available types
TYPE_MAP = {
    None: lambda c, v: None,
    "textarea": to_str,
    "textfield": to_str,
    "iban": to_str,
    "date": lambda c, value: parser.parse(value).date() if value else None,
    "signature": to_str,  # TODO: file like obj?
    "time": lambda c, value: parser.parse(value).time() if value else None,
    "number": noop,
    "phoneNumber": to_str,
    "bsn": to_str,
    "postcode": to_str,
    "file": noop,  # TODO: file like, dict that needs formatting?
    "select": select,
    "radio": to_str,
    "selectboxes": selectboxes,
    "checkbox": noop,
    "email": to_str,
    "map": noop,  # list of coordinates (lng, lat) in float format
    "password": to_str,
    "licenseplate": to_str,
    "currency": lambda c, value: Decimal(str(value)),
}


def convert_if_not_none(converter, component, value):
    if value is None:
        return value
    else:
        return converter(component, value)


def to_python(component: Dict[str, Any], value: Any) -> Any:
    converter = TYPE_MAP.get(component["type"], to_str)

    multiple = component.get("multiple", False)
    if multiple:
        return [convert_if_not_none(converter, component, x) for x in value]
    else:
        return convert_if_not_none(converter, component, value)
