from dataclasses import dataclass
from datetime import date
from typing import Optional

from .base import ZGWModel
from .constants import VertrouwelijkheidsAanduidingen


@dataclass
class Document(ZGWModel):
    url: str
    auteur: str
    identificatie: str
    beschrijving: str
    bestandsnaam: str
    bestandsomvang: int
    bronorganisatie: str
    creatiedatum: date
    formaat: str  # noqa
    indicatie_gebruiksrecht: Optional[dict]
    informatieobjecttype: str
    inhoud: str
    integriteit: dict
    link: str
    ondertekening: Optional[dict]
    ontvangstdatum: Optional[date]
    status: str
    taal: str
    titel: str
    versie: int
    vertrouwelijkheidaanduiding: str
    verzenddatum: Optional[date]
    locked: bool

    def get_vertrouwelijkheidaanduiding_display(self):
        return VertrouwelijkheidsAanduidingen.values[self.vertrouwelijkheidaanduiding]
