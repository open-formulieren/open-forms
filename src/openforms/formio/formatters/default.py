from datetime import datetime
from typing import Any, Dict, List, Union

from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.dateparse import parse_date, parse_time
from django.utils.translation import gettext_lazy as _

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import _join_mapped

from .registry import register


def _get_value_label(possible_values: list, value: str) -> str:
    for possible_value in possible_values:
        if possible_value["value"] == value:
            return possible_value["label"]
    # TODO what if value is not a string? shouldn't it be passed through something to covert for display?
    return value


class FormioFormatter(AbstractBasePlugin):
    def __call__(self, component: dict, value: Any) -> str:
        return self.format(component, value)

    def format(self, component: dict, value: Any) -> str:
        raise NotImplementedError("%r must implement the 'format' method" % type(self))


@register("default")
class DefaultFormatter(FormioFormatter):
    def format(self, component: Dict, value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(v for v in value)
        return str(value)


@register("textfield")
class TextFieldFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return str(value)


@register("email")
class EmailFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return str(value)


@register("date")
class DateFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return _join_mapped(lambda v: fmt_date(parse_date(v)), value)


@register("time")
class TimeFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # strip off the seconds
        return _join_mapped(lambda v: fmt_time(parse_time(v)), value)


@register("phoneNumber")
class PhoneNumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("file")
class FileFormatter(FormioFormatter):
    def format(self, component: Dict, value: List) -> str:
        if value:
            formatted = ", ".join(file["originalName"] for file in value)
        else:
            formatted = _("empty")
        return formatted


@register("textarea")
class TextAreaFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("number")
class NumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("password")
class PasswordFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return "".join("\u25CF" for _ in value)


@register("checkbox")
class CheckboxFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return "ja" if value else "nee"


@register("selectboxes")
class SelectBoxesFormatter(FormioFormatter):
    def format(self, component: Dict, value: List) -> str:
        selected_labels = [
            entry["label"] for entry in component["values"] if value.get(entry["value"])
        ]
        return ", ".join(selected_labels)


@register("select")
class SelectFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        if component.get("appointments", {}).get("showDates", False):
            return _join_mapped(lambda v: fmt_date(parse_date(v)), value)
        elif component.get("appointments", {}).get("showTimes", False):
            # strip off the seconds
            return _join_mapped(lambda v: fmt_time(datetime.fromisoformat(v)), value)
        return _get_value_label(component["data"]["values"], value)


@register("currency")
class CurrencyFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("radio")
class RadioFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return _get_value_label(component["values"], value)


# @register("signature")
class SignatureFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        raise NotImplementedError
