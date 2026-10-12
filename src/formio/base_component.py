"""
Base building blocks for Formio component type definitions.
"""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Mapping, MutableMapping
from typing import (
    Annotated,
    ClassVar,
    Literal,
    Protocol,
    TypeVar,
    dataclass_transform,
)

import msgspec
import structlog
from typing_extensions import TypeIs

from .typing import ComponentValue

logger = structlog.stdlib.get_logger(__name__)


class Sentinel:  # TODO: python 3.15 has built in types for this
    pass


unset = Sentinel()


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

    def __post_init__(self):
        # validate the possible interaction of default value with other attributes, like
        # ``multiple``
        if hasattr(self, "default_value"):
            self._process_default_value(self.default_value, strict=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key!r})"

    def get_label(self) -> str:
        return getattr(self, "label", "") or self.key

    def _process_default_value(
        self,
        value: ComponentValue,
        strict: bool = True,
    ) -> ComponentValue | Sentinel:
        """
        Given a candidate value for ``default_value``, process/normalize it.

        This is called through :meth:`set_default_value` and :meth:`__post_init__`, if
        the component has a ``default_value`` attribute. The former is called in lax
        mode and should be robust, as it may receive prefill data that doesn't properly
        comply with the expected datatypes. When called from the ``__post_init__``, it's
        called in strict mode and invalid/unexpected value types should raise a
        ``ValueError``.
        """
        raise NotImplementedError(
            f"Component type '{type(self)}' must implement '_process_default_value."
        )

    def set_default_value(self, value: ComponentValue) -> None:
        """
        Set the component default value.

        Typically invoked from the prefill machinery which currently still operates on
        the default value, but should eventually switch to just populating the variables
        instead.

        Note that the value can pretty much be any type, including types that aren't
        compatible with the component. The component must be resilient to this, as
        broken data can seep in from external systems and form misconfiguration by
        (functional) administrators.
        """
        if not hasattr(self, "default_value"):
            return

        if (default_value := self._process_default_value(value, strict=False)) is unset:
            log = logger.bind(component=self.type, value=value)
            if supports_multiple(self):
                log = log.bind(multiple=self.multiple)
            log.warning("received_invalid_default_value")
            return

        assert not isinstance(default_value, Sentinel)
        self.default_value = default_value


class MultipleComponent(Protocol):
    multiple: bool


def supports_multiple(component: Component) -> TypeIs[MultipleComponent]:  # pyright: ignore[reportGeneralTypeIssues]
    # the protocol nicely narrows down the union at call sites, but results in a type
    # error here in this function definition... :(
    # Defining MultipleComponent as a subclass of ``Component`` leads to ugly union
    # types at call sites and seems to end up in nominal typing rather than structural
    # typing :sadge:.
    return hasattr(component, "multiple")

