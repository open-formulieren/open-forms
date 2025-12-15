from typing import TypedDict, NotRequired

from openklant_client.types.resources.digitaal_adres import (
    FullForeigKeyRef,
    SoortDigitaalAdres,
)

class ExpectedDigitalAddress(TypedDict):
    """Partial of openklant_client.DigitaalAdres with only necessary properties."""

    adres: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: bool
    verstrektDoorBetrokkene: NotRequired[FullForeigKeyRef | None]
    verstrektDoorPartij: NotRequired[FullForeigKeyRef | None]
