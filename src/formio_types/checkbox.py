from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

import msgspec
import structlog

from openforms.typing import VariableValue

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)

# FIXME: should be Literal["required"], but there is garbage data
type CheckboxValidatorKeys = str

type CheckboxTranslatableProperties = Literal["label", "description", "tooltip"]

CheckboxExtensions = BaseOpenFormsExtensions[CheckboxTranslatableProperties]


class CheckboxValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class Checkbox(Component, tag="checkbox"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: bool = False
    description: str = ""
    errors: Errors[CheckboxValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: CheckboxExtensions | None = None
    placeholder: str = ""  # TODO: remove from TS types
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CheckboxValidatorKeys] | None = None
    validate: CheckboxValidate = msgspec.field(default_factory=CheckboxValidate)

    def set_default_value(self, value: VariableValue) -> None:
        if isinstance(value, bool):
            self.default_value = value
        else:
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
