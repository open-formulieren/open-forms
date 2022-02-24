from datetime import datetime
from typing import Any, Dict, Iterable, List, Union

from django.template.defaultfilters import date as fmt_date, time as fmt_time, yesno
from django.utils.dateparse import parse_date, parse_time
from django.utils.encoding import force_str
from django.utils.formats import number_format
from django.utils.translation import gettext_lazy as _

from glom import glom

from openforms.plugins.plugin import AbstractBasePlugin

from ..typing import OptionDict
from .registry import register


def get_value_label(possible_values: List[OptionDict], value: str) -> str:
    for possible_value in possible_values:
        if possible_value["value"] == value:
            return possible_value["label"]

    assert isinstance(value, str), "Expected value to be a str"

    return value


def join_mapped(value: Any, formatter: callable = str, separator: str = ", ") -> str:
    # map multiple value into a joined string
    # note: filter before passing to this
    # TODO if this stays this simple after the refactoring we can inline and remove it
    return separator.join(map(formatter, value))


class FormioFormatter(AbstractBasePlugin):
    multiple_separator = "; "
    """
    Separator to use for multi-value components.

    Defaults to semi-colon, as formatted numbers already use comma's which hurts
    readability.
    """

    # there is an interesting open question on what to do for empty values
    # currently we're eating them in normalise_value_to_list()
    empty_values = [None, ""]

    def is_empty_value(self, component: dict, value: Any):
        return value in self.empty_values

    def normalise_value_to_list(self, component: dict, value: Any):
        multiple = component.get("multiple", False)
        # note this breaks if multiple is true and value not a list
        value = value if multiple else [value]
        return [v for v in value if not self.is_empty_value(component, v)]

    def join_formatted_values(
        self, component: dict, formatted_values: Iterable[str]
    ) -> str:
        return self.multiple_separator.join(formatted_values)

    def process_result(self, component: dict, formatted: str) -> str:
        return formatted

    def __call__(self, component: dict, value: Any) -> str:
        # note all this depends on value not being unexpected type or shape
        values = self.normalise_value_to_list(component, value)
        formatted_values = (
            force_str(self.format(component, value)) for value in values
        )
        # logically we'd want a .filter_formatted_values() step here
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
        if value is None:
            return []
        else:
            # file component is always a list
            return value

    def process_result(self, component: Dict, formatted: str) -> str:
        # prefix joined filenames to match legacy
        if formatted:
            return _("attachment: %s") % formatted
        return formatted

    def format(self, component: Dict, value: List) -> str:
        # this is only valid for display to the user (because filename component option, dedupe etc)
        return value["originalName"]


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


@register("currency")
class CurrencyFormatter(FormioFormatter):
    def format(self, component: Dict, value: float) -> str:
        # localized and forced to decimalLimit
        # note we mirror formio and default to 2 decimals
        return number_format(value, decimal_pos=component.get("decimalLimit", 2))


@register("radio")
class RadioFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return get_value_label(component["values"], value)


@register("signature")
class SignatureFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        return _("signature added")


@register("map")
class MapFormatter(FormioFormatter):
    def format(self, component: Dict, value: List[float]) -> str:
        # use a comma here since its a single data element
        return join_mapped(value, separator=", ")
