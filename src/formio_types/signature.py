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
type SignatureValidatorKeys = Literal["required"]

type SignatureTranslatableProperties = Literal[
    "label", "description", "tooltip", "footer"
]

SignatureExtensions = BaseOpenFormsExtensions[SignatureTranslatableProperties]


class SignatureValidate(FormioStruct):
    required: bool = False


class Signature(Component, tag="signature"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    description: str = ""
    errors: Errors[SignatureValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    footer: str = ""
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: SignatureExtensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SignatureValidatorKeys] | None = None
    validate: SignatureValidate = msgspec.field(default_factory=SignatureValidate)

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("signature does not support prefill")

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
