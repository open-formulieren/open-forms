from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import msgspec

from ..base_component import BaseOpenFormsExtensions, Component, Conditional
from ..templating import TestWithTrace

type ContentTranslatableProperties = Literal["html"]

ContentExtensions = BaseOpenFormsExtensions[ContentTranslatableProperties]


class Content(Component, tag="content"):
    conditional: Conditional | msgspec.UnsetType = msgspec.UNSET
    custom_class: (
        Literal["", "error", "success", "info", "warning"] | msgspec.UnsetType
    ) = msgspec.UNSET
    hidden: bool = False
    html: str
    open_forms: ContentExtensions | msgspec.UnsetType = msgspec.UNSET
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = False

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.html = do_render(self.html)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.html, attribute="html")
