from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, override

import msgspec
from typing_extensions import deprecated

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
from ..typing import ComponentValue

type CosignV1TranslatableProperties = Literal["label", "description"]

CosignV1Extensions = BaseOpenFormsExtensions[CosignV1TranslatableProperties]


@deprecated(
    "Use the CosignV2 component instead.",
    category=DeprecationWarning,
    stacklevel=2,
)
class CosignV1(Component, tag="coSign"):
    auth_plugin: str = ""
    description: str = ""
    hidden: bool = False
    label: str
    open_forms: CosignV1Extensions | msgspec.UnsetType = msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")


type CosignV2ValidatorKeys = Literal["required"]

type CosignV2TranslatableProperties = Literal["label", "description", "tooltip"]

CosignV2Extensions = BaseOpenFormsExtensions[CosignV2TranslatableProperties]


class CosignV2Validate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class CosignV2(Component, tag="cosign"):
    autocomplete: str = ""
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    default_value: str = ""
    description: str = ""
    errors: Errors[CosignV2ValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: CosignV2Extensions | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CosignV2ValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: CosignV2Validate = msgspec.field(default_factory=CosignV2Validate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> str | Sequence[str] | msgspec.UnsetType:
        match value:
            case str():
                return value
            case None:
                assert strict is False  # enforced at the type level by msgspec
                return ""
        return msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)
        self.default_value = do_render(self.default_value)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
        test_with_trace(self.default_value, attribute="default_value")
