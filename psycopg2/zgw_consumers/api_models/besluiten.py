from dataclasses import dataclass
from datetime import date
from typing import Optional

from .base import ZGWModel
from .constants import VervalRedenen


@dataclass
class Besluit(ZGWModel):
    url: str
    identificatie: str
    verantwoordelijke_organisatie: str
    besluittype: str
    zaak: str
    datum: date
    toelichting: str
    bestuursorgaan: str
    ingangsdatum: date
    vervaldatum: Optional[date]
    vervalreden: str
    vervalreden_weergave: str
    publicatiedatum: Optional[date]
    verzenddatum: Optional[date]
    uiterlijke_reactiedatum: Optional[date]

    def get_vervalreden_display(self) -> str:
        return VervalRedenen.labels[self.vervalreden]


@dataclass
class BesluitDocument(ZGWModel):
    url: str
    informatieobject: str
    besluit: str
