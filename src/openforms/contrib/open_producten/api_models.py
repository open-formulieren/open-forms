from dataclasses import dataclass
from datetime import date
from typing import Optional

from zgw_consumers.api_models.base import Model


@dataclass
class PriceOption(Model):
    id: str
    amount: str
    description: str


@dataclass
class Price(Model):
    id: str
    valid_from: date
    options: list[PriceOption]


@dataclass
class ProductType(Model):
    id: str
    name: str
    current_price: Optional[Price]
    upl_name: str
    upl_uri: str
