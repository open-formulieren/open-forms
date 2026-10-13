from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import msgspec

from ..base_component import BaseOpenFormsExtensions, Component
from ..templating import TestWithTrace

type SoftRequiredErrorsExtensions = BaseOpenFormsExtensions[Literal["html"]]


class SoftRequiredErrors(Component, tag="softRequiredErrors"):
    html: str
    open_forms: SoftRequiredErrorsExtensions | msgspec.UnsetType = msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        pass

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        pass
