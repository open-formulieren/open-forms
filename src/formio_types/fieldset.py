from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

from ._base import BaseOpenFormsExtensions, Component, Conditional, FAQItem
from ._templating import TestWithTrace

type FieldsetTranslatableProperties = Literal["label"]

FieldsetExtensions = BaseOpenFormsExtensions[FieldsetTranslatableProperties]


class Fieldset(Component, tag="fieldset"):
    clear_on_hide: bool = True
    # added in __init__.py because of circular import challenges
    # components: Sequence[AnyComponentSchema]
    conditional: Conditional | None = None
    faq_items: Sequence[FAQItem] = []
    hidden: bool = False
    hide_header: bool = False
    label: str
    open_forms: FieldsetExtensions | None = None
    tooltip: str = ""

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.tooltip = do_render(self.tooltip)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.tooltip, attribute="tooltip")
