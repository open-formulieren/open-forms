from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

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

type NpFamilyMembersValidatorKeys = Literal["required"]

type NpFamilyMembersTranslatableProperties = Literal["label", "description", "tooltip"]

NpFamilyMembersExtensions = BaseOpenFormsExtensions[
    NpFamilyMembersTranslatableProperties
]


class NpFamilyMembersValidate(FormioStruct):
    required: bool = False
    plugins: Sequence[str] = []


@deprecated(
    "Use the partners/children component instead.",
    category=DeprecationWarning,
    stacklevel=2,
)
class NpFamilyMembers(Component, tag="npFamilyMembers"):
    clear_on_hide: bool = True
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    description: str = ""
    errors: Errors[NpFamilyMembersValidatorKeys] | msgspec.UnsetType = msgspec.UNSET
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    include_children: bool = True
    include_partners: bool = True
    is_sensitive_data: bool = True
    label: str
    open_forms: NpFamilyMembersExtensions | msgspec.UnsetType = msgspec.UNSET
    registration: Registration | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = True
    tooltip: str = ""
    translated_errors: (
        TranslatedErrors[NpFamilyMembersValidatorKeys] | msgspec.UnsetType
    ) = msgspec.UNSET
    validate: NpFamilyMembersValidate = msgspec.field(
        default_factory=NpFamilyMembersValidate
    )

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
