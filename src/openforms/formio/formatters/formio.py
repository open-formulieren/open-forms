import logging
from datetime import datetime
from typing import Any

from django.template.defaultfilters import date as fmt_date, time as fmt_time, yesno
from django.utils.dateparse import parse_date, parse_time
from django.utils.formats import number_format
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from glom import glom

from ..typing import Component, OptionDict
from .base import FormatterBase

logger = logging.getLogger(__name__)


def get_value_label(possible_values: list[OptionDict], value: int | str) -> str:
    # From #1466 it's clear that Formio does not force the values to be strings, e.g.
    # if you use numeric values for the options. They are stored as string in the form
    # configuration, but the submitted value is a number.
    # See https://github.com/formio/formio.js/blob/4.12.x/src/components/radio/Radio.js#L208
    # (unmodified in 4.13) but also normalization in the select component
    # https://github.com/formio/formio.js/blob/4.12.x/src/components/select/Select.js#L1227
    _original = value
    # cast to string to compare against the values
    if not isinstance(value, str):
        value = str(value)
        logger.info(
            "Casted original value %r to string value %s for option comparison",
            _original,
            value,
        )

    for possible_value in possible_values:
        if possible_value["value"] == value:
            return possible_value["label"]

    return value


class DefaultFormatter(FormatterBase):
    def format(self, component: Component, value: Any) -> str:
        return str(value)


class TextFieldFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return str(value)


class EmailFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return str(value)


class TimeFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return fmt_time(parse_time(value))


class PhoneNumberFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        # TODO custom formatting?
        return str(value)


class FileFormatter(FormatterBase):
    def normalise_value_to_list(self, component: Component, value: Any):
        if value is None:
            return []
        else:
            # file component is always a list
            return value

    def process_result(self, component: Component, formatted: str) -> str:
        # prefix joined filenames to match legacy
        if formatted:
            return _("attachment: %s") % formatted
        return formatted

    def format(self, component: Component, value: dict) -> str:
        # this is only valid for display to the user (because filename component option, dedupe etc)
        return value["originalName"]


class TextAreaFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        # TODO custom formatting?
        return str(value)


class NumberFormatter(FormatterBase):
    def format(self, component: Component, value: int | float) -> str:
        # localized and forced to decimalLimit
        return number_format(value, decimal_pos=component.get("decimalLimit"))


class PasswordFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        # TODO legacy just printed as-is, but we might want to use unicode-dots or stars
        # return "\u25CF" * len(value)
        return str(value)


class CheckboxFormatter(FormatterBase):
    def format(self, component: Component, value: bool) -> str:
        return str(yesno(value))


class SelectBoxesFormatter(FormatterBase):
    def format(self, component: Component, value: dict[str, bool]) -> str:
        selected_labels = [
            entry["label"] for entry in component["values"] if value.get(entry["value"])
        ]
        return self.multiple_separator.join(selected_labels)


class SelectFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        # grab appointment specific data
        if glom(component, "appointments.showDates", default=False):
            return fmt_date(parse_date(value))
        elif glom(component, "appointments.showTimes", default=False):
            # strip the seconds from a full ISO datetime
            return fmt_time(datetime.fromisoformat(value))
        elif glom(component, "appointments.showLocations", default=False) or glom(
            component, "appointments.showProducts", default=False
        ):
            if isinstance(value, dict):
                return value["name"]
            else:
                # shouldn't happen
                return str(value)
        else:
            # regular value select
            return get_value_label(component["data"]["values"], value)


class CurrencyFormatter(FormatterBase):
    def format(self, component: Component, value: float) -> str:
        # localized and forced to decimalLimit
        # note we mirror formio and default to 2 decimals
        return number_format(value, decimal_pos=component.get("decimalLimit", 2))


class RadioFormatter(FormatterBase):
    def format(self, component: Component, value: str | int) -> str:
        return get_value_label(component["values"], value)


class SignatureFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        text = _("signature added")
        if not self.as_html:
            return text

        assert value.startswith(
            "data:image/"
        ), "Expected 'data:' URI with image mime type"

        # max-width is required for e-mail styling where it may overflow a table cell
        return format_html(
            """<img src="{src}" alt="{alt}" style="max-width: 100%;" />""",
            src=value,
            alt=text,
        )


class AddressNLFormatter(FormatterBase):

    empty_values = ({},)

    def format(component: Component, value: dict[str, str]) -> str:
        return format_html(
            "{postcode} {houseNumber}{houseLetter}{houseNumberAddition}", **value
        )
