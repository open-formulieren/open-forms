from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from ._base import BaseOpenFormsExtensions, Component
from ._templating import TestWithTrace

type SoftRequiredErrorsExtensions = BaseOpenFormsExtensions[Literal["html"]]


class SoftRequiredErrors(Component, tag="softRequiredErrors"):
    html: str
    label: str = ""  # TODO: remove from TS types, is ignored anyway
    open_forms: SoftRequiredErrorsExtensions | None = None

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        pass

    def test_templates(self, test_with_trace: TestWithTrace) -> None:
        pass
