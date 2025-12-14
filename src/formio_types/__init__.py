from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ._base import Component, FormioStruct
from .input import InputComponent
from .layout import Content

# Component types - these cannot be split into the layout.py module due to circular
# import challenges :(


class Fieldset(Component, tag="fieldset"):
    label: str
    components: Sequence[AnyComponent]


class Column(FormioStruct):
    size: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    size_mobile: Literal[1, 2, 3, 4]
    components: Sequence[AnyComponent]


class Columns(Component, tag="columns"):
    columns: Sequence[Column]


type LayoutComponent = Content | Fieldset | Columns

# Discriminated union of all possible component types

type AnyComponent = InputComponent | LayoutComponent
