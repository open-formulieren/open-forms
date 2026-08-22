from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, assert_never

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
type EmailValidatorKeys = str

type EmailTranslatableProperties = Literal["label", "description", "tooltip"]


class EmailExtensions(BaseOpenFormsExtensions[EmailTranslatableProperties]):
    require_verification: bool = False


class EmailValidate(FormioStruct):
    required: bool = False
    max_length: int | None = None
    plugins: Sequence[str] = []


class Email(Component, tag="email"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    confirmation_recipient: bool = False
    default_value: str | Sequence[str] = ""
    description: str = ""
    errors: Errors[EmailValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    multiple: bool = False
    open_forms: EmailExtensions | None = None
    placeholder: str = ""
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[EmailValidatorKeys] | None = None
    validate: EmailValidate = msgspec.field(default_factory=EmailValidate)

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

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case str() if not self.multiple:
                self.default_value = value
            case Sequence() if self.multiple:
                string_values = [x for x in value if isinstance(x, str)]
                self.default_value = string_values
            case None:
                self.default_value = [] if self.multiple else ""
            case _:
                logger.warning(
                    "received_invalid_default_value",
                    component=str(type(self)),
                    value=value,
                    multiple=self.multiple,
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
            test_with_trace(_value, attribute="default_value")
