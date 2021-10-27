import logging
from base64 import b64encode
from datetime import date
from typing import Optional

from django.utils import timezone

from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport

logger = logging.getLogger(__name__)


def create_zaak(
    options: dict,
    payment_required: bool = False,
    existing_reference: str = "",
) -> dict:
    config = ZgwConfig.get_solo()
    client = config.zrc_service.build_client()
    today = date.today().isoformat()
    data = {
        "zaaktype": options["zaaktype"],
        "bronorganisatie": options["organisatie_rsin"],
        "verantwoordelijkeOrganisatie": options["organisatie_rsin"],
        "registratiedatum": today,
        "startdatum": today,
        "omschrijving": "Zaak naar aanleiding van ingezonden formulier",
        "toelichting": "Aangemaakt door Open Formulieren",
        "betalingsindicatie": "nog_niet" if payment_required else "nvt",
    }
    if "vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options["vertrouwelijkheidaanduiding"]

    # add existing (internal) reference if it exists
    if existing_reference:
        data["kenmerken"] = [
            {
                "kenmerk": existing_reference,
                "bron": "Open Formulieren",  # XXX: only 40 chars, what's supposed to go here?
            }
        ]

    zaak = client.create("zaak", data)
    return zaak


def default_get_drc() -> Service:
    config = ZgwConfig.get_solo()
    return config.drc_service


def partial_update_zaak(zaak_url: str, data: dict) -> dict:
    config = ZgwConfig.get_solo()
    client = config.zrc_service.build_client()
    zaak = client.partial_update("zaak", data, url=zaak_url)
    return zaak


def set_zaak_payment(zaak_url: str, partial: bool = False) -> dict:
    data = {
        "betalingsindicatie": "gedeeltelijk" if partial else "geheel",
        "laatsteBetaaldatum": timezone.now().isoformat(),
    }
    return partial_update_zaak(zaak_url, data)


def create_document(
    name: str,
    base64_body: str,
    options: dict,
    get_drc=default_get_drc,
) -> dict:
    client = get_drc().build_client()
    today = date.today().isoformat()

    data = {
        "informatieobjecttype": options["informatieobjecttype"],
        "bronorganisatie": options["organisatie_rsin"],
        "creatiedatum": today,
        "titel": name,
        "auteur": options["author"],
        "taal": options["language"],
        "formaat": options["format"],
        "inhoud": base64_body,
        "status": options["status"],
        "bestandsnaam": options["filename"],
        "beschrijving": options["description"],
    }
    if "vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options["vertrouwelijkheidaanduiding"]

    informatieobject = client.create("enkelvoudiginformatieobject", data)
    return informatieobject


def create_report_document(
    name: str,
    submission_report: SubmissionReport,
    options: dict,
    get_drc=default_get_drc,
) -> dict:
    submission_report.content.seek(0)
    base64_body = b64encode(submission_report.content.read()).decode()

    document_options = {
        "author": "open-forms",
        "language": "nld",
        "format": "application/pdf",
        "status": "definitief",
        "filename": f"open-forms-{name}.pdf",
        "description": "Ingezonden formulier",
    }

    options = {**options, **document_options}

    return create_document(name, base64_body, options, get_drc=get_drc)


def create_csv_document(
    name: str,
    csv_data: str,
    options: dict,
    get_drc=default_get_drc,
) -> dict:
    base64_body = b64encode(csv_data.encode()).decode()

    document_options = {
        "author": "open-forms",
        "language": "nld",
        "format": "text/csv",
        "status": "definitief",
        "filename": f"open-forms-{name}.csv",
        "description": "Ingezonden formulierdata",
    }

    options = {**options, **document_options}

    return create_document(name, base64_body, options, get_drc=get_drc)


def create_attachment_document(
    name: str,
    submission_attachment: SubmissionFileAttachment,
    options: dict,
    get_drc=default_get_drc,
) -> dict:
    client = get_drc().build_client()
    today = date.today().isoformat()

    submission_attachment.content.seek(0)
    base64_body = b64encode(submission_attachment.content.read()).decode()

    document_options = {
        "author": "open-forms",
        "language": "nld",
        "format": submission_attachment.content_type,
        "status": "definitief",
        "filename": submission_attachment.get_display_name(),
        "description": "Bijgevoegd document",
    }

    options = {**options, **document_options}

    return create_document(name, base64_body, options, get_drc=get_drc)


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
    if not rol_typen or not rol_typen.get("results"):
        logger.warning(
            "Roltype specified, but no matching roltype found in the zaaktype.",
            extra={"query_params": query_params},
        )
        return None

    zrc_client = config.zrc_service.build_client()
    data = {
        "zaak": zaak["url"],
        # "betrokkene": initiator.get("betrokkene", ""),
        "betrokkeneType": initiator.get("betrokkeneType", "natuurlijk_persoon"),
        "roltype": rol_typen["results"][0]["url"],
        "roltoelichting": initiator.get("roltoelichting", "inzender formulier"),
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
