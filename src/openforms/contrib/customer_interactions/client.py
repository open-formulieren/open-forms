from __future__ import annotations

from collections.abc import Iterator

from openklant_client.client import OpenKlantClient
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    ListDigitaalAdresParams,
)
from zgw_consumers.client import build_client

from openforms.contrib.client import LoggingMixin

from .models import CustomerInteractionsAPIGroupConfig


def get_customer_interactions_client(
    config: CustomerInteractionsAPIGroupConfig,
) -> CustomerInteractionsClient:
    return build_client(
        config.customer_interactions_service, client_factory=CustomerInteractionsClient
    )


class CustomerInteractionsClient(LoggingMixin, OpenKlantClient):
    def get_digital_addresses_for_bsn(self, bsn: str) -> Iterator[DigitaalAdres]:
        """
        Search digital addresses by BSN of the party.

        The selection of query params and their values are based on the OAS for the
        "partij identificator":
        https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml#tag/partij-identificatoren
        """
        params: ListDigitaalAdresParams = {
            "verstrektDoorPartij__partijIdentificator__codeSoortObjectId": "bsn",
            "verstrektDoorPartij__partijIdentificator__codeRegister": "brp",
            "verstrektDoorPartij__partijIdentificator__codeObjecttype": "natuurlijk_persoon",
            "verstrektDoorPartij__partijIdentificator__objectId": bsn,
        }
        response = self.digitaal_adres.list_iter(params=params)
        yield from response
