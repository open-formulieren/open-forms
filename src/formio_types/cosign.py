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

type CosignV1TranslatableProperties = Literal["label", "description"]

CosignV1Extensions = BaseOpenFormsExtensions[CosignV1TranslatableProperties]


class CosignV1(Component, tag="coSign"):
    auth_plugin: str
    description: str = ""
    hidden: bool = False
    label: str
    open_forms: CosignV1Extensions | None = None

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")


type CosignV2ValidatorKeys = Literal["required"]

type CosignV2TranslatableProperties = Literal["label", "description", "tooltip"]

CosignV2Extensions = BaseOpenFormsExtensions[CosignV2TranslatableProperties]


class CosignV2Validate(FormioStruct):
    required: bool = False


class CosignV2(Component, tag="cosign"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: str = ""
    description: str = ""
    errors: Errors[CosignV2ValidatorKeys] | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: CosignV2Extensions | None = None
    registration: Registration | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CosignV2ValidatorKeys] | None = None
    validate: CosignV2Validate = msgspec.field(default_factory=CosignV2Validate)

    def set_default_value(self, value: VariableValue) -> None:
        match value:
            case str():
                self.default_value = value
            case None:
                self.default_value = ""
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
        self.default_value = do_render(self.default_value)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
        test_with_trace(self.default_value, attribute="default_value")
