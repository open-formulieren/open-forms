from typing import TypedDict

from openklant_client.types.resources.digitaal_adres import SoortDigitaalAdres


class ExpectedDigitalAddress(TypedDict):
    """Partial of openklant_client.DigitaalAdres with only necessary properties."""

    adres: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: bool
