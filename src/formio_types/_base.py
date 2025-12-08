"""
Base building blocks for Formio component type definitions.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Annotated, Literal, TypeVar

import msgspec

__all__ = [
    "Key",
    "Component",
    "Conditional",
    "SupportedLanguage",
    "Errors",
    "TranslatedErrors",
    "PropertyTranslations",
    "BaseOpenFormsExtensions",
    "Prefill",
    "Registration",
]


class ComponentMeta(msgspec.StructMeta):
    def __new__(mcls, name, bases, namespace, **struct_config):
        struct_config.setdefault("tag_field", "type")
        struct_config.setdefault("rename", "camel")
        return super().__new__(mcls, name, bases, namespace, **struct_config)


type Key = Annotated[str, msgspec.Meta(pattern=r"^(\w|\w[\w.\-]*\w)$")]


class Component(msgspec.Struct, metaclass=ComponentMeta, kw_only=True):
    """
    Base structure that any Formio component must satisfy.

    Some (layout) components don't have a label - use the empty string for those.
    """

    id: str = ""
    key: Key


class Conditional(msgspec.Struct, kw_only=True):
    """
    The ``None``/``null`` is not in line with the frontend types, but ``undefined``
    does not exist in JS.

    Note however that formio at runtime uses ``null`` (!).
    """

    show: bool | None = None
    when: Key | None = None
    eq: str | bool | int | float | None = ""  # formio defaults to empty string


type SupportedLanguage = Literal["nl", "en"]

type Errors[KT: str] = MutableMapping[KT, str]

type TranslatedErrors[KT: str] = MutableMapping[SupportedLanguage, Errors[KT]]

P = TypeVar("P", bound=str)  # needs to be defined for msgspec

type PropertyTranslations[P] = Mapping[SupportedLanguage, Mapping[P, str]]


class BaseOpenFormsExtensions[P](msgspec.Struct, kw_only=True):
    translations: PropertyTranslations[P]
    """
    Field properties that can be translated server-side.

    Translation also passed them through the sandboxed template engine.
    """


class Prefill(msgspec.Struct, kw_only=True):
    plugin: str
    attribute: str
    identifier_role: Literal["main", "authorised_person"] = "main"


class Registration(msgspec.Struct, kw_only=True):
    attribute = str
