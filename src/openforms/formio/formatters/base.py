from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from django.utils.encoding import force_str
from django.utils.html import format_html, format_html_join

import structlog

from ..typing import Component

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class FormatterBase[T: Component]:
    as_html: bool = False
    """
    Format for HTML output or not.

    The default is to format for plain text output, but toggling this will emit
    HTML where relevant.
    """
    multiple_separator: str = "; "
    """
    Separator to use for multi-value components.

    Defaults to semi-colon, as formatted numbers already use comma's which hurts
    readability.
    """

    # there is an interesting open question on what to do for empty values
    # currently we're eating them in normalise_value_to_list()
    empty_values: Sequence[Any] = (None, "")

    def is_empty_value(self, component: T, value: Any):
        return value in self.empty_values

    def normalise_value_to_list(self, component: T, value: Any):
        multiple = component.get("multiple", False)
        # this breaks if multiple is true and value not a list
        if multiple:
            if not isinstance(value, (tuple, list)):
                # this happens if value is None
                value = [value]
        else:
            value = [value]
        # convert to list of useful values
        return [v for v in value if not self.is_empty_value(component, v)]

    def join_formatted_values(
        self, component: Component, formatted_values: Iterable[str]
    ) -> str:
        if not self.as_html:
            return self.multiple_separator.join(formatted_values)

        args_generator = ((formatted,) for formatted in formatted_values)
        if component.get("multiple", False):
            return format_html(
                "<ul>{values}</ul>",
                values=format_html_join("", "<li>{}</li>", args_generator),
            )

        return format_html_join(self.multiple_separator, "{}", args_generator)

    def process_result(self, component: T, formatted: str) -> str:
        return formatted

    def __call__(self, component: T, value: Any) -> str:
        # note all this depends on value not being unexpected type or shape
        values = self.normalise_value_to_list(component, value)

        formatted_values = list(
            force_str(self.format(component, value)) for value in values
        )

        # Check if formatted_values isn't empty
        if len(formatted_values) == 0:
            return self.process_result(component, "")

        # logically we'd want a .filter_formatted_values() step here
        return self.process_result(
            component, self.join_formatted_values(component, formatted_values)
        )

    def format(self, component: T, value: Any) -> str:  # pragma:nocover
        raise NotImplementedError("%r must implement the 'format' method" % type(self))
