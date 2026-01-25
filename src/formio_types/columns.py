from __future__ import annotations

from typing import Literal

from ._base import Component, FormioStruct


class Column(FormioStruct):
    size: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    size_mobile: Literal[1, 2, 3, 4] = 4
    # added in __init__.py because of circular import challenges
    # components: Sequence[AnyComponent]


class Columns(Component, tag="columns"):
    clear_on_hide: bool = True
    # added in __init__.py because of circular import challenges
    # columns: Sequence[Column]
    hidden: bool = False
