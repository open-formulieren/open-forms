# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from django.template.defaultfilters import date as fmt_date
from django.utils.dateparse import parse_date

from ..typing import Component
from .base import FormatterBase


class DateFormatter(FormatterBase):
    def format(self, component: Component, value: str) -> str:
        return fmt_date(parse_date(value))


class MapFormatter(FormatterBase):
    def format(self, component: Component, value: list[float]) -> str:
        # use a comma here since its a single data element
        return ", ".join((str(x) for x in value))
