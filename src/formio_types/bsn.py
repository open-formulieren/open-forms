from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FormioStruct,
    Prefill,
    Registration,
    TranslatedErrors,
)

type BSNValidatorKeys = Literal["required"]
type BSNExtensions = BaseOpenFormsExtensions[Literal["label", "description", "tooltip"]]


class BSNValidate(FormioStruct):
    required: bool = False


class BSN(Component, tag="bsn"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # FIXME: missing migration converter and `null` default values exist
    default_value: str | Sequence[str] | None = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[BSNValidatorKeys] | None = None
    hidden: bool = False
    input_mask: Literal["999999999"] = "999999999"
    is_sensitive_data: bool = True
    label: str
    open_forms: BSNExtensions | None = None
    placeholder: str = ""
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[BSNValidatorKeys] | None = None
    validate: BSNValidate | None = None
    validate_on: Literal["blur"] = "blur"
    multiple: bool = False

    def __post_init__(self):
        if self.default_value is None:
            self.default_value = "" if not self.multiple else []

        match (self.multiple, self.default_value):
            case True, str():
                raise ValueError("You must pass a list of values when multiple=True")
            case False, str():
                pass
            case False, Sequence():
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )
