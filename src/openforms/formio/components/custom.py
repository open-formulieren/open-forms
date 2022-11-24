import logging

from openforms.typing import DataMapping
from openforms.utils.date import format_date_value

from ..dynamic_config.date import FormioDateComponent, mutate as mutate_date
from ..formatters.custom import DateFormatter, MapFormatter
from ..formatters.formio import TextFieldFormatter
from ..registry import BasePlugin, register
from ..typing import Component
from ..utils import conform_to_mask

logger = logging.getLogger(__name__)


@register("date")
class Date(BasePlugin):
    formatter = DateFormatter

    @staticmethod
    def normalizer(component: FormioDateComponent, value: str) -> str:
        return format_date_value(value)

    def mutate_config_dynamically(
        self, component: FormioDateComponent, data: DataMapping
    ) -> None:
        """
        Implement the behaviour for our custom date component options.

        In the JS, this component type inherits from Formio datetime component. See
        ``src/openforms/js/components/form/date.js`` for the various configurable options.
        """
        mutate_date(component, data)


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
