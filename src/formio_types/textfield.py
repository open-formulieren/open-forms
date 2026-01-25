from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

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

type TextfieldValidatorKeys = Literal["required", "maxLength", "pattern"]
type TextFieldExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip", "placeholder"]
]


class TextfieldValidate(FormioStruct):
    required: bool = False
    max_length: int | None = None
    pattern: str = ""
    plugins: Sequence[str] = []


class TextField(Component, tag="textfield"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str | Sequence[str] = ""
    derive_city: Annotated[bool, DeprecationWarning] = False
    derive_house_number: Annotated[str, DeprecationWarning] = ""
    derive_postcode: Annotated[str, DeprecationWarning] = ""
    derive_street_name: Annotated[bool, DeprecationWarning] = False
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TextfieldValidatorKeys] | None = None
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: TextFieldExtensions | None = None
    placeholder: str = ""
    prefill: Prefill | None = None
    registration: Registration | None = None
    show_char_count: bool = False
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TextfieldValidatorKeys] | None = None
    validate: TextfieldValidate | None = None
    validate_on: Literal["blur", "change"] = "blur"
    multiple: bool = False

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
