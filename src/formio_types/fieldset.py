from __future__ import annotations

from collections.abc import Collection
from typing import ClassVar, Literal

from ._base import BaseOpenFormsExtensions, Component, Conditional

type FieldsetTranslatableProperties = Literal["label"]

FieldsetExtensions = BaseOpenFormsExtensions[FieldsetTranslatableProperties]


class Fieldset(Component, tag="fieldset"):
    clear_on_hide: bool = True
    # added in __init__.py because of circular import challenges
    # components: Sequence[AnyComponentSchema]
    conditional: Conditional | None = None
    hidden: bool = False
    hide_header: bool = False
    label: str
    open_forms: FieldsetExtensions | None = None
    tooltip: str = ""

    SUPPORTED_TEMPLATE_ATTRIBUTES: ClassVar[Collection[str]] = frozenset(
        ("label", "tooltip")
    )
