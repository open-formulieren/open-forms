from __future__ import annotations

from collections.abc import Iterator

from openklant_client.client import OpenKlantClient
from openklant_client.types.methods.maak_klant_contact import (
    MaakKlantContactCreateData,
    MaakKlantContactResponse,
)
from openklant_client.types.resources import (
    CreatePartijPersoonData,
    Partij,
    PartijListParams,
)
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    DigitaalAdresCreateData,
    ListDigitaalAdresParams,
    SoortDigitaalAdres,
)
from zgw_consumers.client import build_client

from openforms.contrib.client import LoggingMixin
from openforms.submissions.models import Submission
from openforms.translations.utils import to_iso639_2b

from .exceptions import StandardViolation
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

    def create_customer_contact(
        self,
        submission: Submission,
        party_uuid: str | None = None,
    ) -> MaakKlantContactResponse:
        data: MaakKlantContactCreateData = {
            "klantcontact": {
                "kanaal": "Webformulier",
                "onderwerp": submission.form.name,
                "taal": to_iso639_2b(submission.language_code),
                "vertrouwelijk": True,
            },
            "betrokkene": {
                "rol": "klant",
                "initiator": True,
                "organisatienaam": "",
            },
            "onderwerpobject": {
                "onderwerpobjectidentificator": {
                    "objectId": submission.public_registration_reference,
                    "codeObjecttype": "formulierinzending",
                    "codeRegister": "Open Formulieren",
                    "codeSoortObjectId": "public_registration_reference",
                }
            },
        }
        if party_uuid:
            data["betrokkene"]["wasPartij"] = {"uuid": party_uuid}

        return self.methods.maak_klant_contact(data=data)

    def create_digital_address(
        self,
        address: str,
        address_type: SoortDigitaalAdres,
        betrokkene_uuid: str,
        party_uuid: str | None = None,
    ):
        party_data = {"uuid": party_uuid} if party_uuid else None
        data = DigitaalAdresCreateData(
            adres=address,
            soortDigitaalAdres=address_type,
            verstrektDoorBetrokkene={"uuid": betrokkene_uuid},
            verstrektDoorPartij=party_data,
        )
        return self.digitaal_adres.create(data=data)

    def find_party_for_bsn(self, bsn: str) -> Partij | None:
        """
        Search parties by BSN.

        The selection of query params and their values are based on the OAS for the
        "partij identificator":
        https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml#tag/partij-identificatoren
        """

        params: PartijListParams = {
            "partijIdentificator__codeSoortObjectId": "bsn",
            "partijIdentificator__codeRegister": "brp",
            "partijIdentificator__codeObjecttype": "natuurlijk_persoon",
            "partijIdentificator__objectId": bsn,
        }
        response = self.partij.list(params=params)

        if (num_results := len(response["results"])) > 1:
            raise StandardViolation(
                "Combination of 'codeObjecttype', 'codeSoortObjectId', 'objectId' and 'codeRegister' be unique according to the standard."
            )
        if num_results == 0:
            return None

        return response["results"][0]

    def create_party_for_bsn(self, bsn: str) -> Partij:
        data: CreatePartijPersoonData = {
            "soortPartij": "persoon",
            "voorkeurstaal": "nld",
            "indicatieActief": True,
            "digitaleAdressen": None,
            "voorkeursDigitaalAdres": None,
            "rekeningnummers": None,
            "voorkeursRekeningnummer": None,
            "indicatieGeheimhouding": False,
            "partijIdentificatoren": [
                {
                    "partijIdentificator": {
                        "codeSoortObjectId": "bsn",
                        "codeRegister": "brp",
                        "codeObjecttype": "natuurlijk_persoon",
                        "objectId": bsn,
                    }
                }
            ],
            "partijIdentificatie": None,
        }
        return self.partij.create_persoon(data=data)
