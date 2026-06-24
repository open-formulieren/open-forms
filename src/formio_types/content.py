from __future__ import annotations

from typing import Literal

from ._base import BaseOpenFormsExtensions, Component, Conditional, Registration

type ContentTranslatableProperties = Literal["html"]

ContentExtensions = BaseOpenFormsExtensions[ContentTranslatableProperties]


class Content(Component, tag="content"):
    conditional: Conditional | None = None
    custom_class: Literal["", "error", "success", "info", "warning"] = ""
    hidden: bool = False
    html: str
    is_sensitive_data: bool = False  # TODO: remove from TS types - is irrelevant
    label: str = ""  # TODO: remove from TS types, is ignored anyway
    open_forms: ContentExtensions | None = None
    registration: Registration | None = (
        None  # TODO: remove from TS types - is irrelevant
    )
    show_in_email: bool = False
    show_in_pdf: bool = False
    show_in_summary: bool = False

    # keep track of the CSP post processing status...
    _csp_post_processing_done: bool = False
