from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import msgspec

from . import AnyComponent
from ._base import Component

type LayoutComponent = Content | Fieldset | Columns


class Content(Component, kw_only=True, tag="content"):
    html: str


class Fieldset(Component, kw_only=True, tag="fieldset"):
    label: str
    components: Sequence[AnyComponent]


class Column(msgspec.Struct, kw_only=True):
    size: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    size_mobile: Literal[1, 2, 3, 4]
    components: Sequence[AnyComponent]


class Columns(Component, kw_only=True, tag="columns"):
    columns: Sequence[Column]
