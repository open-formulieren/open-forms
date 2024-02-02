import logging

from django.utils import timezone

from furl import furl
from zgw_consumers.nlx import NLXClient

from .catalogi import CatalogiClient
from .utils import get_today

logger = logging.getLogger(__name__)

CRS_HEADERS = {"Content-Crs": "EPSG:4326", "Accept-Crs": "EPSG:4326"}


class ZakenClient(NLXClient):
    def create_zaak(
        self,
        zaaktype: str,
        bronorganisatie: str,
        vertrouwelijkheidaanduiding: str = "",
        payment_required: bool = False,
        existing_reference: str = "",
        **overrides,
    ):
        today = get_today()
        zaak_data = {
            "zaaktype": zaaktype,
            "bronorganisatie": bronorganisatie,
            "verantwoordelijkeOrganisatie": bronorganisatie,
            "registratiedatum": today,
            "startdatum": today,
            "omschrijving": "Zaak naar aanleiding van ingezonden formulier",
            "toelichting": "Aangemaakt door Open Formulieren",
            "betalingsindicatie": "nog_niet" if payment_required else "nvt",
        }

        if vertrouwelijkheidaanduiding:
            zaak_data["vertrouwelijkheidaanduiding"] = vertrouwelijkheidaanduiding

        # add existing (internal) reference if it exists
        if existing_reference:
            zaak_data["kenmerken"] = [
                {
                    "kenmerk": existing_reference,
                    "bron": "Open Formulieren",  # XXX: only 40 chars, what's supposed to go here?
                }
            ]

        zaak_data.update(**overrides)

        response = self.post("zaken", json=zaak_data, headers=CRS_HEADERS)
        response.raise_for_status()

        return response.json()

    def set_payment_status(self, zaak: dict, partial: bool = False):
        data = {
            "betalingsindicatie": "gedeeltelijk" if partial else "geheel",
            "laatsteBetaaldatum": timezone.now().isoformat(),
        }
        response = self.patch(url=zaak["url"], json=data, headers=CRS_HEADERS)
        response.raise_for_status()
        return response.json()

    def create_status(
        self,
        catalogi_client: CatalogiClient,
        zaak: dict,
        initial_status_remarks: str = "",
    ) -> dict:
        # get statustype for initial status
        statustypen = sorted(
            catalogi_client.list_statustypen(zaak["zaaktype"]),
            key=lambda item: item["volgnummer"],
        )
        initial_statustype = statustypen[0]

        # create status
        data = {
            "zaak": zaak["url"],
            "statustype": initial_statustype["url"],
            "datumStatusGezet": timezone.now().isoformat(),
            "statustoelichting": initial_status_remarks,
        }
        response = self.post("statussen", json=data)
        response.raise_for_status()
        return response.json()

    def relate_document(self, zaak: dict, document: dict) -> dict:
        data = {
            "zaak": zaak["url"],
            "informatieobject": document["url"],
        }
        response = self.post("zaakinformatieobjecten", json=data)
        response.raise_for_status()
        return response.json()

    def create_rol(
        self, catalogi_client: CatalogiClient, zaak: dict, betrokkene: dict
    ) -> dict | None:
        roltype = betrokkene.get("roltype")

        if not roltype:
            roltypen_kwargs = {
                "zaaktype": zaak["zaaktype"],
                "omschrijving_generiek": betrokkene.get(
                    "omschrijvingGeneriek", "initiator"
                ),
            }
            rol_typen = catalogi_client.list_roltypen(**roltypen_kwargs)
            if not rol_typen:
                logger.warning(
                    "No matching roltype found in the zaaktype.",
                    extra=roltypen_kwargs,
                )
                return None
            roltype = rol_typen[0]["url"]

        data = {
            "zaak": zaak["url"],
            # "betrokkene": betrokkene.get("betrokkene", ""),
            "betrokkeneType": betrokkene.get("betrokkeneType", "natuurlijk_persoon"),
            "roltype": roltype,
            "roltoelichting": betrokkene.get("roltoelichting", "inzender formulier"),
            "indicatieMachtiging": betrokkene.get("indicatieMachtiging", ""),
            "betrokkeneIdentificatie": betrokkene.get("betrokkeneIdentificatie", {}),
        }

        response = self.post("rollen", json=data)
        response.raise_for_status()

        return response.json()

    def create_zaakobject(
        self, zaak: dict, object: str, objecttype_version: str
    ) -> dict:
        data = {
            "zaak": zaak["url"],
            "object": object,
            "objectType": "overige",
            "objectTypeOverigeDefinitie": {
                "url": objecttype_version,
                "schema": ".jsonSchema",
                "objectData": ".record.data",
            },
        }

        response = self.post("zaakobjecten", json=data)
        response.raise_for_status()

        return response.json()

    def create_zaakeigenschap(self, zaak: dict, eigenschap_data: dict) -> dict:
        zaak_url = zaak["url"]
        data = {
            **eigenschap_data,
            "zaak": zaak_url,
        }
        endpoint = furl(zaak_url) / "zaakeigenschappen"

        response = self.post(endpoint, json=data)
        response.raise_for_status()

        return response.json()
