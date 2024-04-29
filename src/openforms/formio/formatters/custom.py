# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import format_html

from openforms.contrib.brk.constants import AddressValue

from ..typing import Component
from .base import FormatterBase


class DateFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return fmt_date(parse_date(value))


class DateTimeFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        parsed_value = parse_datetime(value)
        return f"{fmt_date(parsed_value)} {fmt_time(parsed_value, 'H:i')}"


class MapFormatter(FormatterBase):
    def format(self, component: Component, value: list[float]) -> str:
        # use a comma here since its a single data element
        return ", ".join((str(x) for x in value))


class AddressNLFormatter(FormatterBase):

    empty_values = ({},)

    def format(self, component: Component, value: AddressValue) -> str:
        value = value.copy()
        value.setdefault("houseLetter", "")
        value.setdefault("houseNumberAddition", "")
        return format_html(
            "{postcode} {houseNumber}{houseLetter} {houseNumberAddition}", **value
        ).strip()


class CosignFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return str(value)
