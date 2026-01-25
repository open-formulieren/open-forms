from __future__ import annotations

from typing import Literal

from typing_extensions import deprecated

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

type NpFamilyMembersValidatorKeys = Literal["required"]


type NpFamilyMembersExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class NpFamilyMembersValidate(FormioStruct):
    required: bool = False


@deprecated(
    "Use the partners/children component instead.",
    category=DeprecationWarning,
    stacklevel=2,
)
class NpFamilyMembers(Component, tag="npFamilyMembers"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    description: str = ""
    errors: Errors[NpFamilyMembersValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: NpFamilyMembersExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[NpFamilyMembersValidatorKeys] | None = None
    validate: NpFamilyMembersValidate | None = None
