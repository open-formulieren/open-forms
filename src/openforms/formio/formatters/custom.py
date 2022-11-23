# TODO implement: iban, bsn, postcode, licenseplate, npFamilyMembers, cosign
from ..typing import Component
from .base import FormatterBase


class MapFormatter(FormatterBase):
    def format(self, component: Component, value: list[float]) -> str:
        # use a comma here since its a single data element
        return ", ".join((str(x) for x in value))
