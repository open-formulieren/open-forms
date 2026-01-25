"""
Base building blocks for Formio component type definitions.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Annotated, Literal, TypeVar, dataclass_transform

import msgspec

__all__ = [
    "Key",
    "Component",
    "FormioStruct",
    "Conditional",
    "SupportedLanguage",
    "Errors",
    "TranslatedErrors",
    "PropertyTranslations",
    "BaseOpenFormsExtensions",
    "Prefill",
    "Registration",
    "Option",
]


@dataclass_transform(kw_only_default=True)
class ComponentMeta(msgspec.StructMeta):
    def __new__(mcls, name, bases, namespace, **struct_config):
        struct_config.setdefault("tag_field", "type")
        struct_config.setdefault("rename", "camel")
        struct_config["kw_only"] = True
        return super().__new__(mcls, name, bases, namespace, **struct_config)


@dataclass_transform(kw_only_default=True)
class FormioStructMeta(msgspec.StructMeta):
    def __new__(mcls, name, bases, namespace, **struct_config):
        struct_config.setdefault("rename", "camel")
        struct_config["kw_only"] = True
        return super().__new__(mcls, name, bases, namespace, **struct_config)


type Key = Annotated[str, msgspec.Meta(pattern=r"^(\w|\w[\w.\-]*\w)$")]
type MaybeEmptyKey = Annotated[str, msgspec.Meta(pattern=r"(^(\w|\w[\w.\-]*\w)$)|(^$)")]


class Component(msgspec.Struct, metaclass=ComponentMeta):
    """
    Base structure that any Formio component must satisfy.

    Some (layout) components don't have a label - use the empty string for those.
    """

    id: str = ""
    key: Key

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key!r})"


class FormioStruct(msgspec.Struct, metaclass=FormioStructMeta):
    """
    Base struct that applies camel case conversion and only accepts keyword arguments.
    """


class Conditional(FormioStruct):
    """
    The ``None``/``null`` is not in line with the frontend types, but ``undefined``
    does not exist in JS.

    Note however that formio at runtime uses ``null`` (!).
    """

    # FIXME: empty strings in existing data
    show: bool | None | Literal[""] = None
    when: MaybeEmptyKey | None = None
    eq: str | bool | int | float | None = ""  # formio defaults to empty string


type SupportedLanguage = Literal["nl", "en"]

type Errors[KT: str] = MutableMapping[KT, str]

type TranslatedErrors[KT: str] = MutableMapping[SupportedLanguage, Errors[KT]]

P = TypeVar("P", bound=str)  # needs to be defined for msgspec

type PropertyTranslations[P] = Mapping[SupportedLanguage, Mapping[P, str]]


class BaseOpenFormsExtensions[P](FormioStruct):
    translations: PropertyTranslations[P] | None = (
        None  # TODO not optional in TS types (!)
    )
    """
    Field properties that can be translated server-side.

    Translation also passed them through the sandboxed template engine.
    """


class Prefill(FormioStruct):
    plugin: str
    attribute: str
    identifier_role: Literal["main", "authorizee"] = "main"


class Registration(FormioStruct):
    attribute = str


# Structs for radio, selectboxes, select...

type OptionTranslations = PropertyTranslations[Literal["label", "description"]]


class OptionExtensions(FormioStruct):
    translations: OptionTranslations | None = None


class Option(FormioStruct):
    value: str
    label: str
    description: str = ""
    open_forms: OptionExtensions | None = None
