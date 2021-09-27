from dataclasses import dataclass

from dateutil.relativedelta import relativedelta

from .base import Model


@dataclass
class ProcesType(Model):
    url: str
    nummer: int
    naam: str
    omschrijving: str
    toelichting: str
    procesobject: str


@dataclass
class Resultaat(Model):
    url: str
    proces_type: ProcesType
    nummer: int
    volledig_nummer: str
    generiek: bool
    specifiek: bool
    naam: str
    omschrijving: str
    herkomst: str
    waardering: str
    procestermijn: str
    procestermijn_weergave: str
    bewaartermijn: relativedelta
    toelichting: str
