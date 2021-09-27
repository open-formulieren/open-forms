from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from .base import ZGWModel
from .catalogi import Eigenschap
from .constants import RolOmschrijving, RolTypes, VertrouwelijkheidsAanduidingen


@dataclass
class Zaak(ZGWModel):
    url: str
    identificatie: str
    bronorganisatie: str
    omschrijving: str
    toelichting: str
    zaaktype: str
    registratiedatum: date
    startdatum: date
    einddatum: Optional[date]
    einddatum_gepland: Optional[date]
    uiterlijke_einddatum_afdoening: Optional[date]
    publicatiedatum: Optional[date]
    vertrouwelijkheidaanduiding: str
    status: str
    resultaat: str
    relevante_andere_zaken: list
    zaakgeometrie: dict

    def get_vertrouwelijkheidaanduiding_display(self):
        return VertrouwelijkheidsAanduidingen.values[self.vertrouwelijkheidaanduiding]


@dataclass
class Status(ZGWModel):
    url: str
    zaak: str
    statustype: str
    datum_status_gezet: datetime
    statustoelichting: str


@dataclass
class ZaakObject(ZGWModel):
    url: str
    zaak: str
    object: str
    object_type: str
    object_type_overige: str
    relatieomschrijving: str
    object_identificatie: Optional[dict]


@dataclass
class ZaakEigenschap(ZGWModel):
    url: str
    # uuid: uuid.UUID
    zaak: str
    eigenschap: str
    naam: str
    waarde: str

    def get_waarde(self) -> Any:
        assert isinstance(
            self.eigenschap, Eigenschap
        ), "Ensure eigenschap has been resolved"
        return self.eigenschap.to_python(self.waarde)


@dataclass
class Resultaat(ZGWModel):
    url: str
    zaak: str
    resultaattype: str
    toelichting: str


@dataclass
class Rol(ZGWModel):
    url: str
    zaak: str
    betrokkene: str
    betrokkene_type: str
    roltype: str
    omschrijving: str
    omschrijving_generiek: str
    roltoelichting: str
    registratiedatum: datetime
    indicatie_machtiging: str
    betrokkene_identificatie: Optional[dict]

    def get_betrokkene_type_display(self):
        return RolTypes.values[self.betrokkene_type]

    def get_omschrijving_generiek_display(self):
        return RolOmschrijving.values[self.omschrijving_generiek]
