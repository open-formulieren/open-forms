from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from typing import Literal

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

type ChildrenTranslatableProperties = Literal["label", "description", "tooltip"]

ChildrenExtensions = BaseOpenFormsExtensions[ChildrenTranslatableProperties]


class ChildDetails(FormioStruct):
    bsn: str
    date_of_birth: date
    first_names: str


class Children(Component, tag="children"):
    clear_on_hide: bool = True
    conditional: Conditional | None = None
    description: str = ""
    enable_selection: bool = False
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    is_sensitive_data: bool = True
    label: str
    open_forms: ChildrenExtensions | None = None
    registration: Registration | None = None
    tooltip: str = ""

    def set_default_value(self, value: VariableValue) -> None:
        raise NotImplementedError("children does not support prefill")

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
        test_with_trace(self.tooltip, attribute="tooltip")
