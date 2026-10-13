"""
Formio component types integration layer.

The top-level formio package uses pure Python (no Django!) definitions and tools to work
with comonent types supported by Open Forms.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import overload

import msgspec

from .base_component import Option, supports_multiple
from .components import (
    BSN,
    IBAN,
    AddressNL,
    AnyComponent,
    Checkbox,
    Children,
    Columns,
    Content,
    CosignV1,
    CosignV2,
    Currency,
    CustomerProfile,
    Date,
    DateTime,
    EditGrid,
    Email,
    Fieldset,
    File,
    LicensePlate,
    Map,
    NpFamilyMembers,
    Number,
    Partners,
    PhoneNumber,
    Postcode,
    Radio,
    Select,
    Selectboxes,
    Signature,
    SoftRequiredErrors,
    Textarea,
    TextField,
    Time,
)
from .templating import get_template_trace_context
from .typing import ComponentDict

# components are ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    "AnyComponent",
    # General purpose functionality
    "Option",
    "supports_multiple",
    "convert_component",
    "convert_components",
    "to_python",
    "get_template_trace_context",
    # Form fields
    "TextField",
    "Email",
    "Date",
    "DateTime",
    "Time",
    "PhoneNumber",
    "Postcode",
    "File",
    "Textarea",
    "Number",
    "Checkbox",
    "Selectboxes",
    "Select",
    "Currency",
    "Radio",
    # Special fields
    "IBAN",
    "LicensePlate",
    "BSN",
    "Signature",
    "CosignV2",
    "Map",
    "EditGrid",
    "AddressNL",
    "Partners",
    "Children",
    "CustomerProfile",
    "NpFamilyMembers",
    "CosignV1",
    # Layout
    "Content",
    "Columns",
    "Fieldset",
    "SoftRequiredErrors",
]


def convert_component(component_dict: ComponentDict) -> AnyComponent:
    """
    Convert a single component definition to a msgspec struct.
    """
    return msgspec.convert(component_dict, type=AnyComponent)


def convert_components(
    component_dicts: Sequence[ComponentDict],
) -> Sequence[AnyComponent]:
    """
    Convert multiple component definitions to msgspec structs.
    """
    return msgspec.convert(component_dicts, type=Sequence[AnyComponent])


@overload
def to_python(obj: AnyComponent) -> ComponentDict: ...


@overload
def to_python(obj: Sequence[AnyComponent]) -> Sequence[ComponentDict]: ...


def to_python(
    obj: AnyComponent | Sequence[AnyComponent],
) -> ComponentDict | Sequence[ComponentDict]:
    """
    Convert back from Python to base types, suitable for JSON serialization.
    """
    return msgspec.to_builtins(obj)
