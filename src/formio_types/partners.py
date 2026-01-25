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

type PartnersExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class PartnerDetails(FormioStruct):
    affixes: str
    bsn: str
    date_of_birth: date
    initials: str
    last_name: str


class Partners(Component, tag="partners"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: Sequence[PartnerDetails] | None = None
    description: str = ""
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    registration: Registration | None = None
    tooltip: str = ""
