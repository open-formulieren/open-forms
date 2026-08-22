from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal

import msgspec
import structlog
from msgspec import Meta

from openforms.typing import VariableValue

from ._base import (
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
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)
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
    conditional: Conditional | None = None
    decimal_limit: Annotated[int, Meta(ge=0, le=9)] | None = None
    default_value: float | None = None
    description: str = ""
    errors: Errors[NumberValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: NumberExtensions | None = None
    prefill: Prefill | None = None
    prefix: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    suffix: str = ""
    tooltip: str = ""
    translated_errors: TranslatedErrors[NumberValidatorKeys] | None = None
    validate: NumberValidate = msgspec.field(default_factory=NumberValidate)

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case float() | int() | None:
                self.default_value = value
            case _:
                logger.warning(
                    "received_invalid_default_value",
                    component=str(type(self)),
                    value=value,
                )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
