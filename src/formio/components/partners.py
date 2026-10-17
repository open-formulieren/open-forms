from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

from ..base_component import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    FAQItem,
    Registration,
)
from ..templating import TestWithTrace

type PartnersTranslatableProperties = Literal["label", "description", "tooltip"]

PartnersExtensions = BaseOpenFormsExtensions[PartnersTranslatableProperties]


class Partners(Component, tag="partners"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    description: str = ""
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: PartnersExtensions | None = None
    registration: Registration | None = None
    tooltip: str = ""

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
