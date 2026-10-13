"""
Formio component types integration layer.

The top-level formio package uses pure Python (no Django!) definitions and tools to work
with comonent types supported by Open Forms.
"""

from __future__ import annotations

from .base_component import supports_multiple
from .components import (
    BSN,
    AddressNL,
    AnyComponent,
    Checkbox,
    Children,
    Content,
    CosignV1,
    CosignV2,
)
from .templating import get_template_trace_context

# components are ordered as they are displayed in the formio builder UI
__all__ = [  # noqa: RUF022
    "AnyComponent",
    # General purpose functionality
    "supports_multiple",
    "get_template_trace_context",
    # Form fields
    "Checkbox",
    # Special fields
    "BSN",
    "CosignV2",
    "AddressNL",
    "Children",
    "CosignV1",
    # Layout
    "Content",
]
