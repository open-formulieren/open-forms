from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal, override

import msgspec
from msgspec import Meta

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

type NumberValidatorKeys = Literal["required", "min", "max"]

type NumberTranslatableProperties = Literal["label", "description", "tooltip"]

NumberExtensions = BaseOpenFormsExtensions[NumberTranslatableProperties]


class NumberValidate(FormioStruct):
    required: bool = False
    min: float | None = None
    max: float | None = None
    plugins: Sequence[str] = []


class Number(Component, tag="number"):
    allow_negative: bool = False
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    decimal_limit: Annotated[int, Meta(ge=0, le=9)] | msgspec.UnsetType = msgspec.UNSET
    default_value: float | None = None
    description: str = ""
    errors: Errors[NumberValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: NumberExtensions | msgspec.UnsetType = msgspec.UNSET
    prefill: Prefill | msgspec.UnsetType = msgspec.UNSET
    prefix: str = ""
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    suffix: str = ""
    tooltip: str = ""
    translated_errors: TranslatedErrors[NumberValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: NumberValidate = msgspec.field(default_factory=NumberValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> float | int | None | msgspec.UnsetType:
        match value:
            case float() | int() | None:
                return value
            case _:
                assert not strict
                return msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
