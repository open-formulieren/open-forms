from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, override

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
from ..typing import ComponentValue

type CheckboxValidatorKeys = Literal["required"]

type CheckboxTranslatableProperties = Literal["label", "description", "tooltip"]

CheckboxExtensions = BaseOpenFormsExtensions[CheckboxTranslatableProperties]


class CheckboxValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


class Checkbox(Component, tag="checkbox"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    default_value: bool = False
    description: str = ""
    errors: Errors[CheckboxValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = False
    label: str
    open_forms: CheckboxExtensions | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: TranslatedErrors[CheckboxValidatorKeys] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    validate: CheckboxValidate = msgspec.field(default_factory=CheckboxValidate)

    @override
    def _process_default_value(
        self, value: ComponentValue, strict: bool = True
    ) -> bool:
        if not strict:
            raise NotImplementedError("checkbox does not support prefill")
        assert isinstance(value, bool)
        return value

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
