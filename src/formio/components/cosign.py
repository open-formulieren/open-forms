from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, override
from typing_extensions import deprecated
type CosignV1TranslatableProperties = Literal["label", "description"]

CosignV1Extensions = BaseOpenFormsExtensions[CosignV1TranslatableProperties]


@deprecated(
    "Use the CosignV2 component instead.",
    category=DeprecationWarning,
    stacklevel=2,
)
class CosignV1(Component, tag="coSign"):
    auth_plugin: str = ""
    description: str = ""
    hidden: bool = False
    label: str
    open_forms: CosignV1Extensions | msgspec.UnsetType = msgspec.UNSET

    def render_templates(self, do_render: Callable[[str], str]) -> None:
        self.label = do_render(self.label)
        self.description = do_render(self.description)

    def _test_templates(self, test_with_trace: TestWithTrace) -> None:
        test_with_trace(self.label, attribute="label")
        test_with_trace(self.description, attribute="description")
