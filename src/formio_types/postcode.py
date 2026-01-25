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

type PostcodeValidatorKeys = Literal["required", "pattern"]
type PostcodeExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class PostcodeValidate(FormioStruct):
    required: bool = False
    pattern: Literal[r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"] = (
        r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$"
    )
    plugins: Sequence[str] = []


class Postcode(Component, tag="postcode"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # FIXME: migration + convert to normalize empty default value
    default_value: str | Sequence[str] | None = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[PostcodeValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: PostcodeExtensions | None = None
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[PostcodeValidatorKeys] | None = None
    validate: PostcodeValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
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
