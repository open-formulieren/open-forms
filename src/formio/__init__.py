"""
Formio component types integration layer.

The top-level formio package uses pure Python (no Django!) definitions and tools to work
with comonent types supported by Open Forms.
"""

from __future__ import annotations

from .base_component import supports_multiple
from .components import (
    BSN,
    IBAN,
    AddressNL,
    AnyComponent,
    Checkbox,
    Children,
    Content,
    CosignV1,
    CosignV2,
    Currency,
    CustomerProfile,
    Date,
    DateTime,
    Email,
    File,
    LicensePlate,
    Map,
    NpFamilyMembers,
    Number,
)
from .templating import get_template_trace_context

# components are ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    "AnyComponent",
    # General purpose functionality
    "supports_multiple",
    "get_template_trace_context",
    # Form fields
    "Email",
    "Date",
    "DateTime",
    "File",
    "Number",
    "Checkbox",
    "Currency",
    # Special fields
    "IBAN",
    "LicensePlate",
    "BSN",
    "CosignV2",
    "Map",
    "AddressNL",
    "Children",
    "CustomerProfile",
    "NpFamilyMembers",
    "CosignV1",
    # Layout
    "Content",
]
