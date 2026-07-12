from __future__ import annotations

from collections.abc import Collection
from typing import ClassVar, Literal

from ._base import BaseOpenFormsExtensions, Component

type SoftRequiredErrorsExtensions = BaseOpenFormsExtensions[Literal["html"]]


class SoftRequiredErrors(Component, tag="softRequiredErrors"):
    html: str
    label: str = ""  # TODO: remove from TS types, is ignored anyway
    open_forms: SoftRequiredErrorsExtensions | None = None

    SUPPORTED_TEMPLATE_ATTRIBUTES: ClassVar[Collection[str]] = frozenset()
