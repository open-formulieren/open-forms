"""
Base building blocks for Formio component type definitions.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import (
    Annotated,
    ClassVar,
    dataclass_transform,
)

import msgspec
import structlog

logger = structlog.stdlib.get_logger(__name__)


@dataclass_transform(kw_only_default=True)
class ComponentMeta(msgspec.StructMeta, ABCMeta):
    """
    Configure the behaviour of the :class:`Component` base class.

    The metaclass avoids having to repeat a bunch of keyword arguments when defining
    msgspec structs that inherit from the base component. In particular, we establish:

    * The ``type`` property (in JSON) is used for the discriminated union to figure out
      which component class to use. This maps to the ``tag`` concept in msgspec structs.
    * JSON typically uses camelCase, while python uses snake_case, so we set up a
      default rename.
    * Forbid positional arguments - many components have 15+ properties with the same
      types being present - enforcing keyword arguments helps readability and makes
      things more explicit.
    * Finally, for every concrete component type, ensure that we can also access it as
      the ``component.type`` attribute, which is quite useful for logging/debugging.
    """

    def __new__(mcls, name, bases, namespace, **struct_config):
        tag: str | None = struct_config.get("tag")
        struct_config.setdefault("tag_field", "type")
        struct_config.setdefault("rename", "camel")
        struct_config["kw_only"] = True
        cls = super().__new__(mcls, name, bases, namespace, **struct_config)
        if tag:
            assert isinstance(tag, str)
            assert issubclass(cls, Component)
            cls.type = tag
        return cls


@dataclass_transform(kw_only_default=True)
class FormioStructMeta(msgspec.StructMeta):
    """
    Configure the behaviour of nested structs inside formio component definitions.

    * Enforce keywords-only behaviour to improve readability.
    * Set up renaming between camelCase and snake_case.
    """

    def __new__(mcls, name, bases, namespace, **struct_config):
        struct_config.setdefault("rename", "camel")
        struct_config["kw_only"] = True
        return super().__new__(mcls, name, bases, namespace, **struct_config)


type Key = Annotated[str, msgspec.Meta(pattern=r"^(\w|\w[\w.\-]*\w)$")]
type MaybeEmptyKey = Annotated[str, msgspec.Meta(pattern=r"(^(\w|\w[\w.\-]*\w)$)|(^$)")]


class Component(msgspec.Struct, metaclass=ComponentMeta):
    """
    Base structure that any Formio component must satisfy.

    Some (layout) components don't have a label - for something label-like, we fall back
    to the key which must always be defined.
    """

    id: str = ""
    """
    Unique component identifier, within the configuration.

    Not relevant for the backend at all, hence the empty default value.

    TODO: it's use may be obsolete now with the formiojs removal - check if it can be
    removed in the typescript types (implying it's not used by renderer or builder).
    """
    key: Key
    """
    The 'address' of the component.

    In Open Forms, unique across an entire form, but not in pure Formio.js (editgrid
    children may have a duplicated key). Together with the namespace from editgrids,
    this does make up unique addresses.
    """
    type: ClassVar[str] = "unknown"  # set by metaclass
    """
    The component type from the msgspec tag exposed as an attribute.

    Set through :class:`ComponentMeta` for each concrete component type class.
    """


    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key!r})"

    def get_label(self) -> str:
        return getattr(self, "label", "") or self.key
