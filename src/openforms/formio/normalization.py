import logging
from abc import abstractmethod
from typing import Any

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.plugins.registry import BaseRegistry

from .typing import Component
from .utils import conform_to_mask

__all__ = ["normalize_value_for_component", "register", "Normalizer"]

logger = logging.getLogger(__name__)


def normalize_value_for_component(component: Component, value: Any) -> Any:
    """
    Given a value (actual or default value) and the component, apply the component-
    specific normalization.
    """
    if (component_type := component.get("type")) not in register:
        return value
    normalizer = register[component_type]
    return normalizer(component, value)


class Registry(BaseRegistry):
    """
    A registry for FormIO normalization functions.
    """

    pass


class Normalizer(AbstractBasePlugin):
    def __call__(self, component: Component, value: Any) -> Any:
        return self.normalize(component, value)

    @abstractmethod
    def normalize(self, component: Component, value: Any) -> Any:
        raise NotImplementedError  # pragma: nocover


# Sentinel to provide the default registry. You an easily instantiate another
# :class:`Registry` object to use as dependency injection in tests.
register = Registry()


@register("postcode")
class PostalCodeNormalizer(Normalizer):
    def normalize(self, component: Component, value: str) -> str:
        if not value:
            return value

        input_mask = component.get("inputMask")
        if not input_mask:
            return value

        try:
            return conform_to_mask(value, input_mask)
        except ValueError:
            logger.warning(
                "Could not conform value '%s' to input mask '%s', returning original value."
            )
            return value
