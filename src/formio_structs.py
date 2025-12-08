"""
Collection of struct definitions that describe the properties of supported formio
component types.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

import msgspec

#
# BASE CLASSES
#


class ComponentMeta(msgspec.StructMeta):
    def __new__(mcls, name, bases, namespace, **struct_config):
        struct_config.setdefault("tag_field", "type")
        struct_config.setdefault("rename", "camel")
        return super().__new__(mcls, name, bases, namespace, **struct_config)


class Component(msgspec.Struct, metaclass=ComponentMeta, kw_only=True):
    """
    Base structure that any Formio component must satisfy.

    Some (layout) components don't have a label - use the empty string for those.
    """

    id: str = ""
    key: Annotated[str, msgspec.Meta(pattern=r"^(\w|\w[\w.\-]*\w)$")]


class CommonOptions:
    description: str = ""
    tooltip: str = ""


#
# LAYOUT components
#
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


#
# INPUT components
#


class TextField(CommonOptions, Component, kw_only=True, tag="textfield"):
    label: str
    multiple: bool = False
    default_value: str | Sequence[str] = ""

    def __post_init__(self):
        if self.multiple ^ isinstance(self.default_value, Sequence):
            raise ValueError(f"The default value type must match {self.multiple=}")


type LayoutComponent = Content | Fieldset | Columns
type InputComponent = TextField
type AnyComponent = InputComponent | LayoutComponent


if __name__ == "__main__":
    comp_def = {
        "id": "so-random",
        "type": "textfield",
        "key": "text.key",
        "label": "A text field!",
        "multiple": True,
        "defaultValue": ["first", "second"],
    }
    content_def = {
        "type": "content",
        "key": "content",
        "label": "",
        "html": "<p>Hello world</p>",
    }

    converted = msgspec.convert([comp_def, content_def], type=Sequence[AnyComponent])

    print(converted)
