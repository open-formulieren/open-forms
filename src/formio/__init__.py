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

__all__ = [  # noqa: RUF022
    "AnyComponent",
    "Option",
    "FormioConfiguration",
    "supports_multiple",
    "convert_component",
    "convert_components",
    "to_python",
    "get_template_trace_context",
    # basic
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
    # special
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
    # layout
    "Content",
    "Columns",
    "Fieldset",
    "SoftRequiredErrors",
    # deprecated
    "CosignV1",
    "NpFamilyMembers",
]


# XXX: there should not be much need for this data structure, as we tend to operate
# on a collection of components directly
class FormioConfiguration(msgspec.Struct, kw_only=True):
    components: Sequence[AnyComponent]


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
