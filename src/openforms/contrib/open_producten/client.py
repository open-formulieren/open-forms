import logging

import requests
from ape_pie import APIClient
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import build_client

from openforms.contrib.open_producten.models import OpenProductenConfig
from openforms.products.models.product import Product

from .types import ActuelePrijsItem, Product as APIProduct, ProductType

logger = logging.getLogger(__name__)


class OpenProductenClient(APIClient):
    def get_current_price(self, product_type_uuid: str) -> ActuelePrijsItem:
        try:
            response = self.get(
                f"producttypen/api/v1/producttypen/{product_type_uuid}/actuele-prijs"
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "exception while fetching current prices from Open Producten",
                exc_info=exc,
            )
            raise exc

        data = response.json()
        current_prices = factory(ActuelePrijsItem, data)
        return current_prices

    def get_product_types(self) -> list[ProductType]:
        try:
            response = self.get("producttypen/api/v1/producttypen")
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "exception while fetching producttypes from Open Producten",
                exc_info=exc,
            )
            raise exc

        data = response.json()
        raw_types = data["results"]
        product_types = factory(ProductType, raw_types)
        return product_types

    def create_product(
        self, product_type: Product, prijs: str, bsn: str = ""
    ) -> APIProduct:
        data = {
            "producttype_uuid": str(product_type.product_type_uuid),
            "prijs": prijs,
            "eigenaren": [{"bsn": "111222333"}],
        }

        try:
            response = self.post("producten/api/v1/producten", json=data)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "exception while creating products from Open Producten",
                exc_info=exc,
            )
            raise exc

        data = response.json()
        return factory(APIProduct, data)


class NoServiceConfigured(RuntimeError):
    pass


def get_open_producten_client() -> OpenProductenClient:
    config = OpenProductenConfig.get_solo()
    if not (service := config.producten_service):
        raise NoServiceConfigured("No open producten service configured!")
    return build_client(service, client_factory=OpenProductenClient)
