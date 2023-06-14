import logging
from base64 import b64encode
from datetime import date
from typing import Callable, List, Optional

from django.utils import timezone

from zgw_consumers.client import ZGWClient
from zgw_consumers.models import Service

from openforms.submissions.models import SubmissionFileAttachment, SubmissionReport
from openforms.translations.utils import to_iso639_2b

logger = logging.getLogger(__name__)


def create_zaak(
    zrc_client: ZGWClient,
    options: dict,
    payment_required: bool = False,
    existing_reference: str = "",
    **extra,
) -> dict:
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
    if "zaak_vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options[
            "zaak_vertrouwelijkheidaanduiding"
        ]

    # add existing (internal) reference if it exists
    if existing_reference:
        data["kenmerken"] = [
            {
                "kenmerk": existing_reference,
                "bron": "Open Formulieren",  # XXX: only 40 chars, what's supposed to go here?
            }
        ]

    data.update(extra)

    zaak = zrc_client.create("zaak", data)
    return zaak


def partial_update_zaak(zrc_client: ZGWClient, zaak_url: str, data: dict) -> dict:
    zaak = zrc_client.partial_update("zaak", data, url=zaak_url)
    return zaak


def set_zaak_payment(
    zrc_client: ZGWClient, zaak_url: str, partial: bool = False
) -> dict:
    data = {
        "betalingsindicatie": "gedeeltelijk" if partial else "geheel",
        "laatsteBetaaldatum": timezone.now().isoformat(),
    }
    return partial_update_zaak(zrc_client, zaak_url, data)


def create_document(
    name: str,
    base64_body: str,
    options: dict,
    get_drc: Callable[[], ZGWClient],
) -> dict:
    drc_client = get_drc()
    today = date.today().isoformat()

    data = {
        "informatieobjecttype": options["informatieobjecttype"],
        "bronorganisatie": options["organisatie_rsin"],
        "creatiedatum": today,
        "titel": name,
        "auteur": options["auteur"],
        "taal": options["language"],
        "formaat": options["format"],
        "inhoud": base64_body,
        "status": options["status"],
        "bestandsnaam": options["filename"],
        "beschrijving": options["description"],
        "indicatieGebruiksrecht": False,
    }
    # map "docVertrouwelijkheidaanduiding" to value that conforms to Document API
    if "doc_vertrouwelijkheidaanduiding" in options:
        data["vertrouwelijkheidaanduiding"] = options["doc_vertrouwelijkheidaanduiding"]

    assert options["auteur"], "auteur must be a non-empty string"

    informatieobject = drc_client.create("enkelvoudiginformatieobject", data)
    return informatieobject


def create_report_document(
    name: str,
    submission_report: SubmissionReport,
    options: dict,
    get_drc: Callable[[], ZGWClient],
) -> dict:
    submission_report.content.seek(0)
    base64_body = b64encode(submission_report.content.read()).decode()

    document_options = {
        "auteur": options.get("auteur") or "Aanvrager",
        "language": to_iso639_2b(submission_report.submission.language_code),
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
    get_drc: Callable[[], ZGWClient],
    language: str = "nld",
) -> dict:
    base64_body = b64encode(csv_data.encode()).decode()

    document_options = {
        "auteur": options.get("auteur") or "Aanvrager",
        "language": language,
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
    get_drc: Callable[[], ZGWClient],
) -> dict:
    submission_attachment.content.seek(0)
    base64_body = b64encode(submission_attachment.content.read()).decode()

    document_options = {
        "auteur": options.get("auteur") or "Aanvrager",
        "language": to_iso639_2b(
            submission_attachment.submission_step.submission.language_code
        ),  # assume same as submission
        "format": submission_attachment.content_type,
        "status": "definitief",
        "filename": submission_attachment.get_display_name(),
        "description": "Bijgevoegd document",
    }

    options = {**options, **document_options}

    titel = options.get("titel") or name

    return create_document(titel, base64_body, options, get_drc=get_drc)


def relate_document(zaak_url: str, document_url: str) -> dict:
    client = Service.get_client(zaak_url)
    data = {"zaak": zaak_url, "informatieobject": document_url}

    zio = client.create("zaakinformatieobject", data)
    return zio


def create_rol(
    zrc_client: ZGWClient,
    ztc_client: ZGWClient,
    zaak: dict,
    betrokkene: dict,
    options: dict,
) -> Optional[dict]:
    roltype = betrokkene.get("roltype")
    if not roltype:
        query_params = {
            "zaaktype": options["zaaktype"],
            "omschrijvingGeneriek": betrokkene.get("omschrijvingGeneriek", "initiator"),
        }
        rol_typen = retrieve_roltypen(query_params=query_params, ztc_client=ztc_client)
        if not rol_typen or not rol_typen:
            logger.warning(
                "No matching roltype found in the zaaktype.",
                extra={"query_params": query_params},
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
    rol = zrc_client.create("rol", data)
    return rol


def match_omschrijving(roltypen: List, omschrijving: str) -> List:
    matches = []
    for roltype in roltypen:
        if roltype.get("omschrijving") == omschrijving:
            matches.append(roltype)
    return matches


def noop_matcher(roltypen: list) -> list:
    return roltypen


def retrieve_roltypen(
    ztc_client: ZGWClient,
    matcher: Callable[[list], list] = noop_matcher,
    query_params: None | dict = None,
) -> List:
    roltypen = ztc_client.list("roltype", query_params)

    return matcher(roltypen["results"])


def create_status(
    zrc_client: ZGWClient,
    ztc_client: ZGWClient,
    zaak: dict,
) -> dict:
    # get statustype for initial status
    statustypen = ztc_client.list("statustype", {"zaaktype": zaak["zaaktype"]})[
        "results"
    ]
    statustype = next(filter(lambda x: x["volgnummer"] == 1, statustypen))

    initial_status_remarks = ""  # variables.get("initialStatusRemarks", "")

    # create status
    data = {
        "zaak": zaak["url"],
        "statustype": statustype["url"],
        "datumStatusGezet": timezone.now().isoformat(),
        "statustoelichting": initial_status_remarks,
    }
    status = zrc_client.create("status", data)
    return status
