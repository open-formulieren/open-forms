from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from typing import Literal

import structlog

from openforms.typing import VariableValue

from ._base import (
    BaseOpenFormsExtensions,
    Component,
    Conditional,
    FAQItem,
    FormioStruct,
    Registration,
)
from ._templating import TestWithTrace

logger = structlog.stdlib.get_logger(__name__)
type PartnersTranslatableProperties = Literal["label", "description", "tooltip"]

PartnersExtensions = BaseOpenFormsExtensions[PartnersTranslatableProperties]


class PartnerDetails(FormioStruct):
    affixes: str
    bsn: str
    date_of_birth: date
    initials: str
    last_name: str


class Partners(Component, tag="partners"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    default_value: Sequence[PartnerDetails] | None = None
    description: str = ""
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: PartnersExtensions | None = None
    registration: Registration | None = None
    tooltip: str = ""

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("partners does not support prefill")

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
