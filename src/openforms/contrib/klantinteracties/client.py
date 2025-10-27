from typing import Literal, TypedDict

from zgw_consumers.client import build_client

from openforms.utils.api_clients import pagination_helper

from ..client import LoggingClient
from .models import KlantinteractiesConfig


def get_klantinteracties_client() -> "KlantinteractiesClient":
    config = KlantinteractiesConfig.get_solo()
    assert config.service is not None
    return build_client(config.service, client_factory=KlantinteractiesClient)


class DigitaleAdres(TypedDict, total=False):
    url: str
    adres: str
    soortDigitaalAdres: Literal["email", "telefoonnummer", "overig"]
    isStandaardAdres: bool


class KlantinteractiesClient(LoggingClient):
    def get_digital_addresses_for_bsn(self, bsn: str) -> list[DigitaleAdres]:
        response = self.get(
            "digitaleadressen",
            params={
                "verstrektDoorPartij__partijIdentificator__codeObjecttype": "natuurlijk_persoon",
                "verstrektDoorPartij__partijIdentificator__codeRegister": "brp",
                "verstrektDoorPartij__partijIdentificator__codeSoortObjectId": "bsn",
                "verstrektDoorPartij__partijIdentificator__objectId": bsn,
            },
        )
        response.raise_for_status()
        data = response.json()
        return list(pagination_helper(self, data))
