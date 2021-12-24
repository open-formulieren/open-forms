from typing import Any, Dict

from openforms.plugins.plugin import AbstractBasePlugin

from .registry import register


class FormioFormatter(AbstractBasePlugin):
    def __call__(self, component: dict, value: Any) -> str:
        return self.format(component, value)

    def format(self, component: dict, value: Any) -> str:
        raise NotImplementedError("%r must implement the 'format' method" % type(self))


@register("default")
class DefaultFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        if isinstance(value, list):
            return value
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
        raise NotImplementedError


@register("time")
class TimeFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("phoneNumber")
class PhoneNumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("file")
class FileFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("textarea")
class TextAreaFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("number")
class NumberFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("password")
class PasswordFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("checkbox")
class CheckboxFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("selectboxes")
class SelectBoxesFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        selected_labels = [
            entry["label"] for entry in component["values"] if value.get(entry["value"])
        ]
        return ", ".join(selected_labels)


@register("select")
class SelectFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("currency")
class CurrencyFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


@register("radio")
class RadioFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError


# @register("signature")
class SignatureFormatter(FormioFormatter):
    def format(self, component: Dict, value: str) -> str:
        raise NotImplementedError
