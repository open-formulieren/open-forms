from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Union

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from .base import Model, ZGWModel, factory


@dataclass
class Catalogus(ZGWModel):
    url: str
    domein: str
    rsin: str
    contactpersoon_beheer_emailadres: str
    contactpersoon_beheer_naam: str
    contactpersoon_beheer_telefoonnummer: str
    besluittypen: list
    informatieobjecttypen: list
    zaaktypen: list


@dataclass
class ZaakType(ZGWModel):
    url: str
    catalogus: str
    identificatie: str
    omschrijving: str
    omschrijving_generiek: str
    vertrouwelijkheidaanduiding: str
    doel: str
    aanleiding: str
    toelichting: str
    indicatie_intern_of_extern: str
    handeling_initiator: str
    onderwerp: str
    handeling_behandelaar: str
    doorlooptijd: relativedelta
    servicenorm: Optional[relativedelta]
    opschorting_en_aanhouding_mogelijk: bool
    verlenging_mogelijk: bool
    verlengingstermijn: Optional[relativedelta]
    trefwoorden: list
    publicatie_indicatie: bool
    publicatietekst: str
    verantwoordingsrelatie: list
    producten_of_diensten: list
    # selectielijst_procestype: ProcesType
    statustypen: list
    resultaattypen: list
    eigenschappen: list
    informatieobjecttypen: list
    roltypen: list
    besluittypen: list
    deelzaaktypen: list

    begin_geldigheid: date
    einde_geldigheid: Optional[date]
    versiedatum: date
    concept: bool


@dataclass
class StatusType(ZGWModel):
    url: str
    zaaktype: str
    omschrijving: str
    omschrijving_generiek: str
    statustekst: str
    volgnummer: int
    is_eindstatus: bool


@dataclass
class InformatieObjectType(ZGWModel):
    url: str
    catalogus: str
    omschrijving: str
    vertrouwelijkheidaanduiding: str
    begin_geldigheid: date
    einde_geldigheid: Optional[date]
    concept: bool


@dataclass
class ResultaatType(ZGWModel):
    url: str
    zaaktype: str
    omschrijving: str
    resultaattypeomschrijving: str
    omschrijving_generiek: str
    selectielijstklasse: str
    toelichting: str
    archiefnominatie: str
    archiefactietermijn: Optional[relativedelta]
    brondatum_archiefprocedure: dict


@dataclass
class EigenschapSpecificatie(Model):
    groep: str
    formaat: str
    lengte: str
    kardinaliteit: str
    waardenverzameling: list  # List[str]


EIGENSCHAP_FORMATEN = {
    "tekst": str,
    "getal": lambda val: Decimal(val.replace(",", ".")),
    "datum": date.fromisoformat,
    "datum_tijd": parse,
}


@dataclass
class Eigenschap(ZGWModel):
    url: str
    zaaktype: str
    naam: str
    definitie: str
    specificatie: dict
    toelichting: str

    def __post_init__(self):
        super().__post_init__()
        self.specificatie = factory(EigenschapSpecificatie, self.specificatie)

    def to_python(self, value: str) -> Union[str, Decimal, date, datetime]:
        """
        Cast the string value into the appropriate python type based on the spec.
        """
        formaat = self.specificatie.formaat
        assert formaat in EIGENSCHAP_FORMATEN, f"Unknown format {formaat}"

        converter = EIGENSCHAP_FORMATEN[formaat]
        return converter(value)


@dataclass
class RolType(ZGWModel):
    url: str
    zaaktype: str
    omschrijving: str
    omschrijving_generiek: str


@dataclass
class BesluitType(ZGWModel):
    url: str
    catalogus: str
    omschrijving: str
    omschrijving_generiek: str
    besluitcategorie: str
    reactietermijn: Optional[relativedelta]
    publicatie_indicatie: bool
    publicatietekst: str
    publicatietermijn: Optional[relativedelta]
    toelichting: str
    zaaktypen: List[str]
    informatieobjecttypen: List[str]
    begin_geldigheid: date
    einde_geldigheid: Optional[date]
    concept: bool
