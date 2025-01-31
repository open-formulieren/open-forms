# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from datetime import date
from typing import NotRequired, TypedDict

from django.template.defaultfilters import date as fmt_date, time as fmt_time
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..typing import AddressNLComponent, Component
from .base import FormatterBase


class DateFormatter(FormatterBase):
    def format(self, component: Component, value: str | date | None) -> str:
        if isinstance(value, str):
            value = parse_date(value)
        return fmt_date(value)


class DateTimeFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        parsed_value = parse_datetime(value)
        return f"{fmt_date(parsed_value)} {fmt_time(parsed_value, 'H:i')}"


class MapFormatter(FormatterBase):
    def format(self, component: Component, value: list[float]) -> str:
        # use a comma here since its a single data element
        return ", ".join((str(x) for x in value))


class AddressValue(TypedDict):
    """
    Redefined, as the BRK structure is converted to snake_case.

    The Formio data is not transformed, and it stays camelCased. So while it's the same
    data, the shape is different.
    """

    postcode: str
    houseNumber: str
    houseLetter: NotRequired[str]
    houseNumberAddition: NotRequired[str]
    city: NotRequired[str]
    streetName: NotRequired[str]
    secretStreetCity: NotRequired[str]


class AddressNLFormatter(FormatterBase):

    empty_values = ({},)

    def format(self, component: AddressNLComponent, value: AddressValue) -> str:
        value = value.copy()
        value.setdefault("houseLetter", "")
        value.setdefault("houseNumberAddition", "")
        value.setdefault("city", "")
        value.setdefault("streetName", "")

        short_template = "{postcode} {houseNumber}{houseLetter} {houseNumberAddition}"
        full_template = (
            "{streetName} {houseNumber}{houseLetter} {houseNumberAddition}"
            "{sep}{postcode} {city}"
        )

        # setdefault doesn't narrow it for the type checker :(
        assert "city" in value
        assert "streetName" in value
        template = (
            full_template if (value["city"] or value["streetName"]) else short_template
        )

        if self.as_html:
            sep = mark_safe("<br>")
            return format_html(template, sep=sep, **value)

        return template.format(sep="\n", **value).strip()


class CosignFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return str(value)
