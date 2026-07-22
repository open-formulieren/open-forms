from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal, assert_never

import msgspec

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
from ._templating import TestWithTrace

type TextfieldValidatorKeys = Literal["required", "maxLength", "pattern"]


type TextFieldTranslatableProperties = Literal[
    "label", "description", "tooltip", "placeholder"
]
TextFieldExtensions = BaseOpenFormsExtensions[TextFieldTranslatableProperties]


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
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
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

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.placeholder = do_render(self.placeholder)
        self.tooltip = do_render(self.tooltip)

        match self.default_value:
            case str():
                self.default_value = do_render(self.default_value)
            case Sequence():
                self.default_value = [do_render(v) for v in self.default_value]
            case _:  # pragma: no cover
                assert_never(self.default_value)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.placeholder, attribute="placeholder")
        test_with_trace(self.tooltip, attribute="tooltip")

        normalized = (
            self.default_value
            if isinstance(self.default_value, Sequence)
            else [self.default_value]
        )
        for _value in normalized:
            test_with_trace(_value or "", attribute="default_value")
