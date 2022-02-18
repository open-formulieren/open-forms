from typing import Any, Dict, Iterable, List, Union

from django.template.defaultfilters import date as fmt_date, time as fmt_time, yesno
from django.utils.dateparse import parse_date, parse_time
from django.utils.encoding import force_str
from django.utils.formats import number_format
from django.utils.translation import gettext_lazy as _

from openforms.plugins.plugin import AbstractBasePlugin

from .registry import register


def _get_value_label(possible_values: list, value: str) -> str:
    for possible_value in possible_values:
        if possible_value["value"] == value:
            return possible_value["label"]

    assert isinstance(value, str), "Expected value to be a str"

    return value


# NOTE filtering with bool() is evil and might eat zeros, False etc
# this only still here for dev/debug/review purposes
# def _get_values(value: Any, filter_func=bool) -> List[Any]:
#     """
#     Filter a single or multiple value into a list of acceptable values.
#     """
#     # normalize values into a list
#     if not isinstance(value, (list, tuple)):
#         value = [value]
#     return [item for item in value if filter_func(item)]


def _join_mapped(value: Any, formatter: callable = str, seperator: str = ", ") -> str:
    # map multiple value into a joined string
    # note: filter before passing to this
    return seperator.join(map(formatter, value))


class FormioFormatter(AbstractBasePlugin):
    empty_display = ""  # _("empty")
    multiple_separator = "; "  # ", "
    empty_values = [None, ""]

    def is_empty(self, component: dict, value: Any):
        return value in self.empty_values

    def normalise_value_to_list(self, component: dict, value: Any):
        multiple = component.get("multiple", False)
        value = value if multiple else [value]
        return [v for v in value if not self.is_empty(component, v)]

    def join_formatted_values(
        self, component: dict, formatted_values: Iterable[str]
    ) -> str:
        return self.multiple_separator.join(formatted_values)

    def process_result(self, component: dict, formatted: str) -> str:
        return formatted

    def __call__(self, component: dict, value: Any) -> str:
        values = self.normalise_value_to_list(
            component, value
        )  # normalize to list of values
        formatted_values = (
            force_str(self.format(component, value)) for value in values
        )
        return self.process_result(
            component, self.join_formatted_values(component, formatted_values)
        )

    def format(self, component: dict, value: Any) -> str:
        raise NotImplementedError("%r must implement the 'format' method" % type(self))


@register("default")
class DefaultFormatter(FormioFormatter):
    def format(self, component: Dict, value: Any) -> str:
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
        return fmt_date(parse_date(value))


@register("time")
class TimeFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return fmt_time(parse_time(value))


@register("phoneNumber")
class PhoneNumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("file")
class FileFormatter(FormioFormatter):
    def normalise_value_to_list(self, component: dict, value: Any):
        # file component is always a list
        return value

    def process_result(self, component: Dict, formatted: str) -> str:
        # prefix joined filenames to match legacy
        if formatted:
            return _("attachment: %s") % formatted
        return formatted

    def format(self, component: Dict, value: List) -> str:
        if value:
            formatted = value["originalName"]
        else:
            # TODO do we even need this branch?
            formatted = self.empty_display
        return formatted


@register("textarea")
class TextAreaFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO custom formatting?
        return str(value)


@register("number")
class NumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: Union[int, float]) -> str:
        # localized and forced to decimalLimit
        return number_format(value, decimal_pos=component.get("decimalLimit"))


@register("password")
class PasswordFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO legacy just printed as-is, but we might want to use unicode-dots or stars
        # return "\u25CF" * len(value)
        return str(value)


@register("checkbox")
class CheckboxFormatter(FormioFormatter):
    def format(self, component: Dict, value: bool) -> str:
        return yesno(value)


@register("selectboxes")
class SelectBoxesFormatter(FormioFormatter):
    def format(self, component: Dict, value: Dict[str, bool]) -> str:
        selected_labels = [
            entry["label"] for entry in component["values"] if value.get(entry["value"])
        ]
        return self.multiple_separator.join(selected_labels)


@register("select")
class SelectFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        # TODO re-enable this untested code
        # if component.get("appointments", {}).get("showDates", False):
        #     return _join_mapped(value, lambda v: fmt_date(parse_date(v)))
        # elif component.get("appointments", {}).get("showTimes", False):
        #     # strip off the seconds
        #     return _join_mapped( value, lambda v: fmt_time(datetime.fromisoformat(v)))
        return _get_value_label(component["data"]["values"], value)


@register("currency")
class CurrencyFormatter(FormioFormatter):
    def format(self, component: Dict, value: float) -> str:
        # localized and forced to decimalLimit
        # NOTE we mirror formio and default to 2 decimals
        return number_format(value, decimal_pos=component.get("decimalLimit") or 2)


@register("radio")
class RadioFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return _get_value_label(component["values"], value)


@register("signature")
class SignatureFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        if value:
            return _("signature added")
        else:
            return ""


@register("map")
class MapFormatter(FormioFormatter):
    def format(self, component: Dict, value: List[float]) -> str:
        # use a comma here since its a single data element
        return _join_mapped(value, str, ", ")
