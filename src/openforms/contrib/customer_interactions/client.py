from __future__ import annotations

from collections.abc import Iterator
from typing import assert_never

from openklant_client.client import OpenKlantClient
from openklant_client.types.common import ForeignKeyRef
from openklant_client.types.iso_639_2 import LanguageCode
from openklant_client.types.methods.maak_klant_contact import (
    MaakKlantContactCreateData,
    MaakKlantContactResponse,
)
from openklant_client.types.resources import (
    CreatePartijOrganisatieData,
    CreatePartijPersoonData,
    Partij,
    PartijListParams,
)
from openklant_client.types.resources.digitaal_adres import (
    DigitaalAdres,
    DigitaalAdresCreateData,
    DigitaalAdresPartialUpdateData,
    ListDigitaalAdresParams,
    SoortDigitaalAdres,
)
from zgw_consumers.client import build_client

from openforms.contrib.client import LoggingMixin
from openforms.submissions.models import Submission
from openforms.translations.utils import to_iso639_2b

from ...authentication.constants import AuthAttribute
from .exceptions import StandardViolation
from .models import CustomerInteractionsAPIGroupConfig


def get_customer_interactions_client(
    config: CustomerInteractionsAPIGroupConfig,
) -> CustomerInteractionsClient:
    return build_client(
        config.customer_interactions_service, client_factory=CustomerInteractionsClient
    )


class CustomerInteractionsClient(LoggingMixin, OpenKlantClient):
    def _get_digital_addresses_for_bsn(self, bsn: str) -> Iterator[DigitaalAdres]:
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

    def _get_digital_addresses_for_kvk(self, kvk: str) -> Iterator[DigitaalAdres]:
        """
        Search digital addresses by KVK number of the party.

        The selection of query params and their values are based on the OAS for the
        "partij identificator":
        https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml#tag/partij-identificatoren
        """
        params: ListDigitaalAdresParams = {
            "verstrektDoorPartij__partijIdentificator__codeSoortObjectId": "kvk_nummer",
            "verstrektDoorPartij__partijIdentificator__codeRegister": "hr",
            "verstrektDoorPartij__partijIdentificator__codeObjecttype": "niet_natuurlijk_persoon",
            "verstrektDoorPartij__partijIdentificator__objectId": kvk,
        }
        response = self.digitaal_adres.list_iter(params=params)
        yield from response

    def _get_digital_addresses_for_kvk_branch_number(
        self, vestigingsnummer: str
    ) -> Iterator[DigitaalAdres]:
        """
        Search digital addresses by branch number of the party.

        The selection of query params and their values are based on the OAS for the
        "partij identificator":
        https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml#tag/partij-identificatoren
        """
        params: ListDigitaalAdresParams = {
            "verstrektDoorPartij__partijIdentificator__codeSoortObjectId": "vestigingsnummer",
            "verstrektDoorPartij__partijIdentificator__codeRegister": "hr",
            "verstrektDoorPartij__partijIdentificator__codeObjecttype": "vestiging",
            "verstrektDoorPartij__partijIdentificator__objectId": vestigingsnummer,
        }
        response = self.digitaal_adres.list_iter(params=params)
        yield from response

    def get_digital_addresses(
        self,
        auth_attribute: AuthAttribute,
        auth_value: str,
        legal_subject_service_restriction: str = "",
    ) -> Iterator[DigitaalAdres]:
        match auth_attribute:
            case AuthAttribute.bsn:
                return self._get_digital_addresses_for_bsn(bsn=auth_value)

            case AuthAttribute.kvk:
                if legal_subject_service_restriction:
                    return self._get_digital_addresses_for_kvk_branch_number(
                        vestigingsnummer=legal_subject_service_restriction
                    )
                return self._get_digital_addresses_for_kvk(kvk=auth_value)

            case AuthAttribute.pseudo | AuthAttribute.employee_id:  # pragma: no cover
                raise NotImplementedError(
                    "Only bsn and kvk authentications are supported for Customer Interactions API"
                )

            case _:  # pragma: no cover
                assert_never(auth_attribute)

    def get_digital_address_for_party(
        self, address: str, party_uuid: str
    ) -> DigitaalAdres:
        params: ListDigitaalAdresParams = {
            "verstrektDoorPartij__uuid": party_uuid,
            "adres": address,
        }
        response = self.digitaal_adres.list_iter(params=params)

        digitaal_adres = next(response)
        return digitaal_adres

    def create_customer_contact(
        self,
        submission: Submission,
        party_uuid: str = "",
    ) -> MaakKlantContactResponse:
        language_code: LanguageCode = to_iso639_2b(submission.language_code)  # pyright: ignore[reportAssignmentType]
        data: MaakKlantContactCreateData = {
            "klantcontact": {
                "kanaal": "Webformulier",
                "onderwerp": submission.form.name,
                "taal": language_code,
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
        is_preferred: bool,
        betrokkene_uuid: str,
        party_uuid="",
    ) -> DigitaalAdres:
        party_data: ForeignKeyRef | None = {"uuid": party_uuid} if party_uuid else None
        data = DigitaalAdresCreateData(
            adres=address,
            soortDigitaalAdres=address_type,
            isStandaardAdres=is_preferred,
            verstrektDoorBetrokkene={"uuid": betrokkene_uuid},
            verstrektDoorPartij=party_data,
            omschrijving="",
        )
        return self.digitaal_adres.create(data=data)

    def update_digital_address_for_party(
        self, address: str, party_uuid: str, is_preferred: bool
    ) -> DigitaalAdres:
        """
        find an address for the party and update its preference
        """
        digital_address = self.get_digital_address_for_party(address, party_uuid)

        data = DigitaalAdresPartialUpdateData(isStandaardAdres=is_preferred)
        return self.digitaal_adres.partial_update(
            uuid=digital_address["uuid"], data=data
        )

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
                "Combination of 'codeObjecttype', 'codeSoortObjectId', 'objectId' and 'codeRegister' "
                "must be unique according to the standards."
            )
        if num_results == 0:
            return None

        return response["results"][0]

    def find_party_for_kvk(self, kvk: str) -> Partij | None:
        """
        Search parties by KVK number.

        The selection of query params and their values are based on the OAS for the
        "partij identificator":
        https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml#tag/partij-identificatoren
        """

        params: PartijListParams = {
            "partijIdentificator__codeSoortObjectId": "kvk_nummer",
            "partijIdentificator__codeRegister": "hr",
            "partijIdentificator__codeObjecttype": "niet_natuurlijk_persoon",
            "partijIdentificator__objectId": kvk,
        }
        response = self.partij.list(params=params)

        if (num_results := len(response["results"])) > 1:
            raise StandardViolation(
                "Combination of 'codeObjecttype', 'codeSoortObjectId', 'objectId' and 'codeRegister' "
                "must be unique according to the standards."
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
            "partijIdentificatie": {"contactnaam": None},
        }
        return self.partij.create_persoon(data=data)

    def create_party_for_kvk(self, kvk: str) -> Partij:
        data: CreatePartijOrganisatieData = {
            "soortPartij": "organisatie",
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
                        "codeSoortObjectId": "kvk_nummer",
                        "codeRegister": "hr",
                        "codeObjecttype": "niet_natuurlijk_persoon",
                        "objectId": kvk,
                    }
                }
            ],
            "partijIdentificatie": {"naam": ""},
        }
        return self.partij.create_organisatie(data=data)

    def get_or_create_party(
        self, auth_attribute: AuthAttribute, auth_value: str
    ) -> tuple[Partij, bool]:
        party: Partij
        created: bool

        match auth_attribute:
            case AuthAttribute.bsn:
                existing_party = self.find_party_for_bsn(auth_value)
                if existing_party:
                    party = existing_party
                    created = False

                else:
                    party = self.create_party_for_bsn(auth_value)
                    created = True

                return party, created

            case AuthAttribute.kvk:
                existing_party = self.find_party_for_kvk(auth_value)
                if existing_party:
                    party = existing_party
                    created = False

                else:
                    party = self.create_party_for_kvk(auth_value)
                    created = True

                return party, created

            case AuthAttribute.pseudo | AuthAttribute.employee_id:
                raise NotImplementedError(
                    "Only bsn and kvk authentications are supported for Customer Interactions API"
                )

            case _:  # pragma: no cover
                assert_never(auth_attribute)
