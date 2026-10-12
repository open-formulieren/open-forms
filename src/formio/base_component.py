"""
Base building blocks for Formio component type definitions.
"""

from __future__ import annotations

from abc import ABCMeta
from collections.abc import Iterator, Mapping, MutableMapping
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

type AnyComponent = Component


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

    Not relevant for the backend at all, hence the empty default value, but it is used
    as input for the React ``key`` in the renderer.
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

    def iter_children(self) -> Iterator[tuple[AnyComponent, str]]:
        """
        Return an iterator producing child components of this component.

        The iterator value is a tuple of ``(component, namespace)`` so that edit grid
        namespaces can be properly passed along.
        """
        yield from ()

    def _process_default_value(
        self,
        value: ComponentValue,
        strict: bool = True,
    ) -> ComponentValue | msgspec.UnsetType:
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

        if (
            default_value := self._process_default_value(value, strict=False)
        ) is msgspec.UNSET:
            log = logger.bind(component=self.type, value=value)
            if supports_multiple(self):
                log = log.bind(multiple=self.multiple)
            log.warning("received_invalid_default_value")
            return

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

    show: bool | None = None
    when: MaybeEmptyKey | None = None
    # formio defaults to empty string - make sure the renderer has the same behaviour
    # if this is changed here
    eq: str | bool | int | float | None = ""


type SupportedLanguage = Literal["nl", "en"]

type Errors[KT: str] = MutableMapping[KT, str]

type TranslatedErrors[KT: str] = MutableMapping[SupportedLanguage, Errors[KT]]

P = TypeVar("P", bound=str)  # needs to be defined for msgspec

type PropertyTranslations[P] = Mapping[SupportedLanguage, Mapping[P, str]]


class BaseOpenFormsExtensions[P](FormioStruct):
    translations: PropertyTranslations[P] | msgspec.UnsetType = msgspec.UNSET
    """
    Field properties that can be translated server-side.

    Translation machinery also passes them through the sandboxed template engine.

    Note that this property is not optional in the TS types, but for DX reasons we make
    it optional in the backend as it cuts down on boilerplate.
    """


class Prefill(FormioStruct):
    """
    Component-level prefill settings.

    When plugin and attribute are empty strings, prefill is not configured.
    """

    plugin: str
    attribute: str
    identifier_role: Literal["main", "authorizee"] = "main"


class Registration(FormioStruct):
    attribute: str


# Structs for radio, selectboxes, select...

type OptionTranslations = PropertyTranslations[Literal["label", "description"]]


class OptionExtensions(FormioStruct):
    translations: OptionTranslations | msgspec.UnsetType = msgspec.UNSET


class Option(FormioStruct):
    value: str
    label: str
    description: str = ""
    open_forms: OptionExtensions | msgspec.UnsetType = msgspec.UNSET


# Structs for FAQ items, which support translations as well

type FAQItemTranslations = PropertyTranslations[Literal["label", "content"]]


class FAQItemExtensions(FormioStruct):
    translations: FAQItemTranslations | msgspec.UnsetType = msgspec.UNSET


class FAQItem(FormioStruct):
    id: str
    label: str
    content: str
    open_forms: FAQItemExtensions | msgspec.UnsetType = msgspec.UNSET
