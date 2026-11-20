from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

import msgspec

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    Errors,
    FAQItem,
    FormioStruct,
    Registration,
    TranslatedErrors,
)
from ..templating import TestWithTrace

type SignatureValidatorKeys = Literal["required"]

type SignatureTranslatableProperties = Literal[
    "label", "description", "tooltip", "footer"
]

SignatureExtensions = BaseOpenFormsExtensions[SignatureTranslatableProperties]


class SignatureValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class Signature(Component, tag="signature"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    description: str = ""
    errors: Errors[SignatureValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    footer: str = ""
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: SignatureExtensions | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[SignatureValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: SignatureValidate = msgspec.field(default_factory=SignatureValidate)

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
