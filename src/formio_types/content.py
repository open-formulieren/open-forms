from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import msgspec

from ._base import BaseOpenFormsExtensions, Component, Conditional
from ._templating import TestWithTrace

type ContentTranslatableProperties = Literal["html"]

ContentExtensions = BaseOpenFormsExtensions[ContentTranslatableProperties]


class Content(Component, tag="content"):
    conditional: Conditional | None = None
    custom_class: Literal["", "error", "success", "info", "warning"] | None = ""
    hidden: bool = False
    html: str
    label: str = ""  # TODO: remove from TS types, is ignored anyway
    open_forms: ContentExtensions | None = None
    show_in_email: bool = False
    show_in_pdf: bool = msgspec.field(name="showInPDF", default=True)
    show_in_summary: bool = False

    # keep track of the CSP post processing status...
    _csp_post_processing_done: bool = False

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.html = do_render(self.html)
        # DeprecationWarning
        self.label = do_render(self.label)

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.html, attribute="html")
        # DeprecationWarning
        test_with_trace(self.label, attribute="label")
