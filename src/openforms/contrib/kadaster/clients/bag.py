from dataclasses import dataclass

import elasticapm
import requests
import structlog
from opentelemetry import trace

from openforms.contrib.hal_client import HALClient
from openforms.formio.components.utils import salt_location_message

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.contrib.kadaster.clients.bag")


@dataclass
class AddressResult:
    street_name: str
    city: str
    secret_street_city: str = ""


class BAGClient(HALClient):
    """
    Client for the LV BAG API.

    Documentation: https://lvbag.github.io/BAG-API/Technische%20specificatie/Redoc/

    NOTE: this is apparently also part of Haal Centraal:
    https://vng-realisatie.github.io/Haal-Centraal-BAG-bevragen/getting-started

    This client is expected to work with both v1 and v2 of the API's.
    """

    @tracer.start_as_current_span(
        name="get-address",
        attributes={"span.type": "app", "span.subtype": "bag", "span.action": "query"},
    )
    @elasticapm.capture_span(span_type="app.bag.query")
    def get_address(
        self, postcode: str, house_number: str, reraise_errors: bool = False
    ) -> AddressResult:
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
            logger.exception("bag_request_failure", exc_info=exc)
            return self.build_address_result(postcode, house_number)

        response_data = response.json()
        if "_embedded" not in response_data:
            # No addresses were found
            return self.build_address_result(postcode, house_number)

        first_result = response_data["_embedded"]["adressen"][0]
        street_name = first_result.pop("korteNaam")
        city = first_result.pop("woonplaatsNaam")

        return self.build_address_result(postcode, house_number, city, street_name)

    def build_address_result(
        self, postcode: str, house_number: str, city: str = "", street_name: str = ""
    ) -> AddressResult:
        secret_street_city = salt_location_message(
            {
                "postcode": postcode.upper().replace(" ", ""),
                "number": house_number,
                "city": city,
                "street_name": street_name,
            }
        )

        return AddressResult(
            street_name=street_name,
            city=city,
            secret_street_city=secret_street_city,
        )
