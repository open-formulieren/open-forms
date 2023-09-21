import logging
from dataclasses import dataclass

import elasticapm
import requests

from openforms.contrib.hal_client import HALClient

logger = logging.getLogger(__name__)


@dataclass
class AddressResult:
    street_name: str
    city: str


class BAGClient(HALClient):
    """
    Client for the LV BAG API.

    Documentation: https://lvbag.github.io/BAG-API/Technische%20specificatie/Redoc/
    """

    @elasticapm.capture_span(span_type="app.bag.query")
    def get_address(
        self, postcode: str, house_number: str, reraise_errors: bool = False
    ) -> AddressResult | None:
        params = {
            "huisnummer": house_number,
            "postcode": postcode.replace(" ", ""),
        }

        try:
            response = self.get("adressen", params=params)
            response.raise_for_status()
        except requests.RequestException as exc:
            if reraise_errors:
                raise exc
            logger.exception(
                "Could not retrieve address details from the BAG API", exc_info=exc
            )
            return None

        response_data = response.json()
        if "_embedded" not in response_data:
            # No addresses were found
            return None

        first_result = response_data["_embedded"]["adressen"][0]
        return AddressResult(
            street_name=first_result.pop("korteNaam"),
            city=first_result.pop("woonplaatsNaam"),
        )
