"""
Formio component types integration layer.

The top-level formio package uses pure Python (no Django!) definitions and tools to work
with comonent types supported by Open Forms.
"""

from __future__ import annotations

from collections.abc import Sequence

import msgspec

from .base_component import supports_multiple
from .components import (
    BSN,
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
    Iban,
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

__all__ = [  # noqa: RUF022
    "AnyComponent",
    "FormioConfiguration",
    "supports_multiple",
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
    "Iban",
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


class FormioConfiguration(msgspec.Struct, kw_only=True):
    components: Sequence[AnyComponent]
