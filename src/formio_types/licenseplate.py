from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Registration,
    TranslatedErrors,
)

type LicensePlateValidatorKeys = Literal["required"]
type LicensePlateExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class LicensePlateValidate(FormioStruct):
    required: bool = False
    # these backslashes don't look right :thinking:
    pattern: Literal[r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"] = (
        r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"
    )


class LicensePlate(Component, tag="licenseplate"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    description: str = ""
    # FIXME: some existing data has persisted `errors`
    errors: Errors[LicensePlateValidatorKeys | Literal["pattern"]] | None = None
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    multiple: bool = False
    open_forms: LicensePlateExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[LicensePlateValidatorKeys] | None = None
    validate: LicensePlateValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"

    def __post_init__(self):
        match (self.multiple, self.default_value):
            case True, str():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )
