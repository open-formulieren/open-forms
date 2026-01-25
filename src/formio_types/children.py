from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Literal

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    FormioStruct,
    Registration,
)

type ChildrenExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class ChildDetails(FormioStruct):
    bsn: str
    date_of_birth: date
    first_names: str


class Children(Component, tag="children"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: Sequence[ChildDetails] | None = None
    description: str = ""
    enable_selection: bool = False
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    registration: Registration | None = None
    tooltip: str = ""
