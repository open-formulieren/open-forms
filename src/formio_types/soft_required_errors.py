from __future__ import annotations

from typing import Literal

from ._base import BaseOpenFormsExtensions, Component

type SoftRequiredErrorsExtensions = BaseOpenFormsExtensions[Literal["html"]]


class SoftRequiredErrors(Component, tag="softRequiredErrors"):
    html: str
    label: str = ""  # TODO: remove from TS types, is ignored anyway
    open_forms: SoftRequiredErrorsExtensions | None = None
