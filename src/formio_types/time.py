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

type TimeValidatorKeys = Literal["required", "minTime", "maxTime", "invalid_time"]
type TimeExtensions = BaseOpenFormsExtensions[
    Literal["label", "description", "tooltip"]
]


class DateTimeValidate(FormioStruct):
    required: bool = False
    # FIXME: should be time instances, but can't deserialize empty string into a valid
    # time, nor is conversion to non viable at this point.
    # We should be pretty flexible in updating the JS types as this is our own feature,
    # it's not vanilla Formio.
    min_time: str | None = ""
    max_time: str | None = ""


class Time(Component, tag="time"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    # FIXME: properly parse this into ``time`` instances, but then we need to
    # pre-process for empty strings & add ``null`` to the allowed types in the frontend.
    default_value: str | Sequence[str] = ""
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TimeValidatorKeys] | None = None
    format: Literal["HH:mm"] = "HH:mm"
    hidden: bool = False
    input_type: Literal["text"] = "text"
    is_sensitive_data: bool = False
    label: str
    open_forms: TimeExtensions | None = None
    placeholder: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = True
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TimeValidatorKeys] | None = None
    validate: DateTimeValidate | None = None
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
