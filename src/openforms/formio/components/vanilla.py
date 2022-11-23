"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""
from openforms.utils.date import format_date_value

from ..formatters.formio import (
    CheckboxFormatter,
    CurrencyFormatter,
    DateFormatter,
    DefaultFormatter,
    EmailFormatter,
    FileFormatter,
    NumberFormatter,
    PasswordFormatter,
    PhoneNumberFormatter,
    RadioFormatter,
    SelectBoxesFormatter,
    SelectFormatter,
    SignatureFormatter,
    TextAreaFormatter,
    TextFieldFormatter,
    TimeFormatter,
)
from ..registry import BasePlugin, register
from ..typing import Component


@register("default")
class Default(BasePlugin):
    """
    Fallback for unregistered component types, implementing default behaviour.
    """

    formatter = DefaultFormatter


@register("textfield")
class TextField(BasePlugin):
    formatter = TextFieldFormatter


@register("email")
class Email(BasePlugin):
    formatter = EmailFormatter


@register("date")
class Date(BasePlugin):
    formatter = DateFormatter

    @staticmethod
    def normalizer(component: Component, value: str) -> str:
        return format_date_value(value)


@register("time")
class Time(BasePlugin):
    formatter = TimeFormatter


@register("phoneNumber")
class PhoneNumber(BasePlugin):
    formatter = PhoneNumberFormatter


@register("file")
class File(BasePlugin):
    formatter = FileFormatter


@register("textarea")
class TextArea(BasePlugin):
    formatter = TextAreaFormatter


@register("number")
class Number(BasePlugin):
    formatter = NumberFormatter


@register("password")
class Password(BasePlugin):
    formatter = PasswordFormatter


@register("checkbox")
class Checkbox(BasePlugin):
    formatter = CheckboxFormatter


@register("selectboxes")
class SelectBoxes(BasePlugin):
    formatter = SelectBoxesFormatter


@register("select")
class Select(BasePlugin):
    formatter = SelectFormatter


@register("currency")
class Currency(BasePlugin):
    formatter = CurrencyFormatter


@register("radio")
class Radio(BasePlugin):
    formatter = RadioFormatter


@register("signature")
class Signature(BasePlugin):
    formatter = SignatureFormatter
