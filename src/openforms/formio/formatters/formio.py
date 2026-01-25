from collections.abc import Sequence
from datetime import time
from typing import Any

from django.template.defaultfilters import time as fmt_time, yesno
from django.utils.formats import number_format
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext, gettext_lazy as _

import structlog

from formio_types import (
    AnyComponent,
    Checkbox,
    Currency,
    Email,
    File,
    Number,
    Option,
    PhoneNumber,
    Radio,
    Select,
    Selectboxes,
    Signature,
    Textarea,
    TextField,
    Time,
)

from .base import FormatterBase

logger = structlog.stdlib.get_logger(__name__)


def get_value_label(possible_values: Sequence[Option], value: int | str) -> str:
    # From #1466 it's clear that Formio does not force the values to be strings, e.g.
    # if you use numeric values for the options. They are stored as string in the form
    # configuration, but the submitted value is a number.
    # See https://github.com/formio/formio.js/blob/4.12.x/src/components/radio/Radio.js#L208
    # (unmodified in 4.13) but also normalization in the select component
    # https://github.com/formio/formio.js/blob/4.12.x/src/components/select/Select.js#L1227
    _original = value
    # cast to string to compare against the values
    # TODO: check logs if this is still necessary
    if not isinstance(value, str):
        value = str(value)
        logger.info(
            "formio.formatter_cast_to_string",
            original=_original,
            value=value,
        )

    for possible_value in possible_values:
        if possible_value.value == value:
            return possible_value.label

    return value


class DefaultFormatter(FormatterBase[AnyComponent]):
    def format(self, component: AnyComponent, value: Any) -> str:
        return str(value)


class TextFieldFormatter(FormatterBase[TextField]):
    def format(self, component: TextField, value: str) -> str:
        return str(value)


class EmailFormatter(FormatterBase[Email]):
    def format(self, component: Email, value: str) -> str:
        return str(value)


class TimeFormatter(FormatterBase[Time]):
    def format(self, component: Time, value: time | None) -> str:
        return fmt_time(value)


class PhoneNumberFormatter(FormatterBase[PhoneNumber]):
    def format(self, component: PhoneNumber, value: str) -> str:
        # TODO custom formatting?
        return str(value)


class FileFormatter(FormatterBase[File]):
    def normalise_value_to_list(self, component: File, value: Any):
        if value is None:
            return []
        else:
            # file component is always a list
            return value

    def process_result(self, component: File, formatted: str) -> str:
        if not formatted:
            return ""

        # Make sure we don't mangle safe-strings!
        if self.as_html:
            return formatted
        else:
            return _("attachment: %s") % formatted

    def format(self, component: File, value: dict) -> str:
        # this is only valid for display to the user (because filename component option, dedupe etc)
        return value["originalName"]


class TextAreaFormatter(FormatterBase[Textarea]):
    def format(self, component: Textarea, value: str) -> str:
        # TODO custom formatting?
        return str(value)


class NumberFormatter(FormatterBase[Number]):
    def format(self, component: Number, value: int | float) -> str:
        # localized and forced to decimalLimit
        return number_format(value, decimal_pos=component.decimal_limit)


class CheckboxFormatter(FormatterBase[Checkbox]):
    def format(self, component: Checkbox, value: bool) -> str:
        return str(yesno(value))


class SelectBoxesFormatter(FormatterBase[Selectboxes]):
    def format(self, component: Selectboxes, value: dict[str, bool]) -> str:
        selected_labels = [
            entry.label for entry in component.values if value.get(entry.value)
        ]
        if self.as_html:
            # For the html output, wrap the values in li tags and put it inside an ul tag.
            # The selectboxes formatter handles all values at the same time,
            # so handle the full html formatting here.
            if not selected_labels:
                return ""
            return format_html(
                "<ul>{values}</ul>",
                values=format_html_join(
                    "",
                    "<li>{}</li>",
                    ((selected_label,) for selected_label in selected_labels),
                ),
            )
        return self.multiple_separator.join(selected_labels)


class SelectFormatter(FormatterBase[Select]):
    def format(self, component: Select, value: str) -> str:
        values = component.data.values
        assert isinstance(value, str)
        return get_value_label(values, value)


class CurrencyFormatter(FormatterBase[Currency]):
    def format(self, component: Currency, value: float) -> str:
        # localized and forced to decimalLimit
        # note we mirror formio and default to 2 decimals
        return number_format(value, decimal_pos=component.decimal_limit or 2)


class RadioFormatter(FormatterBase[Radio]):
    def format(self, component: Radio, value: str | int) -> str:
        return get_value_label(component.values, value)


class SignatureFormatter(FormatterBase[Signature]):
    def format(self, component: Signature, value: str) -> str:
        text = gettext("signature added")
        if not self.as_html:
            return text

        assert value.startswith("data:image/"), (
            "Expected 'data:' URI with image mime type"
        )

        # max-width is required for e-mail styling where it may overflow a table cell
        return format_html(
            """<img src="{src}" alt="{alt}" style="max-width: 100%;" />""",
            src=value,
            alt=text,
        )
