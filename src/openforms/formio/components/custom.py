import logging

from ..formatters.custom import MapFormatter
from ..formatters.formio import TextFieldFormatter
from ..registry import BasePlugin, register
from ..typing import Component
from ..utils import conform_to_mask

logger = logging.getLogger(__name__)


@register("map")
class Map(BasePlugin):
    formatter = MapFormatter


@register("postcode")
class Postcode(BasePlugin):
    formatter = TextFieldFormatter

    @staticmethod
    def normalizer(component: Component, value: str) -> str:
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
