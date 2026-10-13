from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal, assert_never, override

import msgspec

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Prefill,
    Registration,
    TranslatedErrors,
)
from ..templating import TestWithTrace
from ..typing import ComponentValue

type TextfieldValidatorKeys = Literal["required", "maxLength", "pattern"]


type TextFieldTranslatableProperties = Literal[
    "label", "description", "tooltip", "placeholder"
]
TextFieldExtensions = BaseOpenFormsExtensions[TextFieldTranslatableProperties]


class TextfieldValidate(FormioStruct):
    required: bool = False
    max_length: int | msgspec.UnsetType = msgspec.UNSET
    pattern: str = ""
    plugins: Sequence[str] = []


class TextField(Component, tag="textfield"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    default_value: str | Sequence[str] = ""
    derive_city: Annotated[bool, DeprecationWarning] = False
    derive_house_number: Annotated[str, DeprecationWarning] = ""
    derive_postcode: Annotated[str, DeprecationWarning] = ""
    derive_street_name: Annotated[bool, DeprecationWarning] = False
    description: str = ""
    disabled: bool = False  # should be 'read_only'
    errors: Errors[TextfieldValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    multiple: bool = False
    open_forms: TextFieldExtensions | msgspec.UnsetType = msgspec.UNSET
    placeholder: str = ""
    prefill: Prefill | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_char_count: bool = False
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[TextfieldValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: TextfieldValidate = msgspec.field(default_factory=TextfieldValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> str | Sequence[str] | msgspec.UnsetType:
        match (self.multiple, value):
            case False, str():
                return value
            case True, str() if strict:
                raise ValueError("You must pass a list of values when multiple=True")
            case True, Sequence():
                string_values = [x for x in value if isinstance(x, str)]
                return string_values
            case False, Sequence() if strict:
                raise ValueError(
                    "You must pass a string default_value when multiple=False"
                )
            case _, None:
                assert strict is False  # enforced at the type level by msgspec
                return [] if self.multiple else ""
        return msgspec.UNSET

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

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
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
