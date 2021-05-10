import json
from base64 import b64encode
from datetime import date
from typing import Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_apis.models import ZgwConfig


def create_zaak(options: dict) -> dict:
    config = ZgwConfig.get_solo()
    client = config.zrc_service.build_client()
    today = date.today().isoformat()
    data = {
        "zaaktype": options["zaaktype"],
        "bronorganisatie": options["organisatie_rsin"],
        "verantwoordelijkeOrganisatie": options["organisatie_rsin"],
        "registratiedatum": today,
        "startdatum": today,
        "omschrijving": 'Zaak naar aanleiding van ingezonden formulier "{form_name}".',
        "toelichting": "Aangemaakt door Open Formulieren",
        # "betalingsindicatie": "nvt",
    }
    if "vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options["vertrouwelijkheidaanduiding"]

    zaak = client.create("zaak", data)
    return zaak


def create_document(name: str, body: dict, options: dict) -> dict:
    config = ZgwConfig.get_solo()
    client = config.drc_service.build_client()
    today = date.today().isoformat()
    # TODO is a json document what we want?
    base64_body = b64encode(json.dumps(body, cls=DjangoJSONEncoder).encode()).decode()
    data = {
        "informatieobjecttype": options["informatieobjecttype"],
        "bronorganisatie": options["organisatie_rsin"],
        "creatiedatum": today,
        "titel": name,
        "auteur": "openforms",
        "taal": "nld",
        "inhoud": base64_body,
        "status": "definitief",
        "bestandsnaam": f"{today}-{name}.txt",
        "beschrijving": "Ingezonden formulier",
    }
    if "vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options["vertrouwelijkheidaanduiding"]

    informatieobject = client.create("enkelvoudiginformatieobject", data)
    return informatieobject


def relate_document(zaak_url: str, document_url: str) -> dict:
    client = Service.get_client(zaak_url)
    data = {"zaak": zaak_url, "informatieobject": document_url}

    zio = client.create("zaakinformatieobject", data)
    return zio


def create_rol(zaak: dict, initiator: dict, options: dict) -> Optional[dict]:
    config = ZgwConfig.get_solo()
    ztc_client = config.ztc_service.build_client()
    query_params = {
        "zaaktype": options["zaaktype"],
        "omschrijvingGeneriek": initiator.get("omschrijvingGeneriek", "initiator"),
    }
    rol_typen = ztc_client.list("roltype", query_params)
    if not rol_typen:
        # logger.info(
        #     "Roltype specified, but no matching roltype found in the zaaktype.",
        #     extra={"query_params": query_params},
        # )
        return None

    zrc_client = config.zrc_service.build_client()
    data = {
        "zaak": zaak["url"],
        # "betrokkene": initiator.get("betrokkene", ""),
        "betrokkeneType": initiator.get("betrokkeneType", "natuurlijk_persoon"),
        "roltype": rol_typen["results"][0]["url"],
        "roltoelichting": initiator.get("roltoelichting", ""),
        "indicatieMachtiging": initiator.get("indicatieMachtiging", ""),
        "betrokkeneIdentificatie": initiator.get("betrokkeneIdentificatie", {}),
    }
    rol = zrc_client.create("rol", data)
    return rol


def create_status(zaak: dict) -> dict:
    config = ZgwConfig.get_solo()

    # get statustype for initial status
    ztc_client = config.ztc_service.build_client()
    statustypen = ztc_client.list("statustype", {"zaaktype": zaak["zaaktype"]})[
        "results"
    ]
    statustype = next(filter(lambda x: x["volgnummer"] == 1, statustypen))

    initial_status_remarks = ""  # variables.get("initialStatusRemarks", "")

    # create status
    zrc_client = config.zrc_service.build_client()
    data = {
        "zaak": zaak["url"],
        "statustype": statustype["url"],
        "datumStatusGezet": timezone.now().isoformat(),
        "statustoelichting": initial_status_remarks,
    }
    status = zrc_client.create("status", data)
    return status
