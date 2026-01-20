from dataclasses import dataclass
from datetime import date
from typing import Optional

from zgw_consumers.api_models.base import Model


@dataclass
class PrijsOptie(Model):
    uuid: str
    bedrag: str
    beschrijving: str


@dataclass
class Prijs(Model):
    uuid: str
    prijsopties: list[PrijsOptie]
    actief_vanaf: date


@dataclass
class ProductType(Model):
    uuid: str
    naam: str
    prijzen: list[Prijs]
    parameters: dict
    samenvatting: str


@dataclass
class ProductTypeOptie(Model):
    uuid: str
    bedrag: float
    beschrijving: str


@dataclass
class ActuelePrijs(Model):
    uuid: str
    actief_vanaf: date
    prijsopties: list[ProductTypeOptie]


@dataclass
class ActuelePrijsItem(Model):
    uuid: str
    actuele_prijs: Optional[ActuelePrijs]
