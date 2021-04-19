import json
from base64 import b64encode
from datetime import date

from django.core.serializers.json import DjangoJSONEncoder

from zgw_consumers.models import Service

from .models import ZgwConfig, ZGWFormConfig


def create_zaak(form_config: ZGWFormConfig) -> dict:
    config = ZgwConfig.get_solo()
    client = config.zrc_service.build_client()
    today = date.today().isoformat()
    data = {
        "zaaktype": form_config.zaaktype,
        "bronorganisatie": form_config.organisatie_rsin,
        "verantwoordelijkeOrganisatie": form_config.organisatie_rsin,
        "registratiedatum": today,
        "startdatum": today,
        # "omschrijving": "TODO",
        # "toelichting": "TODO",
        "vertrouwelijkheidaanduiding": form_config.vertrouwelijkheidaanduiding,
        # "betalingsindicatie": "nvt",
        # "selectielijstklasse": "TODO",
        # "archiefnominatie": "vernietigen",
    }

    zaak = client.create("zaak", data)
    return zaak


def create_document(name: str, body: dict, form_config: ZGWFormConfig) -> dict:
    config = ZgwConfig.get_solo()
    client = config.drc_service.build_client()
    today = date.today().isoformat()
    base64_body = b64encode(json.dumps(body, cls=DjangoJSONEncoder).encode()).decode()
    data = {
        "informatieobjecttype": form_config.informatieobjecttype,
        "bronorganisatie": form_config.organisatie_rsin,
        "creatiedatum": today,
        "titel": name,
        "auteur": "openforms",
        "taal": "nld",
        "inhoud": base64_body,
        "vertrouwelijkheidaanduiding": form_config.vertrouwelijkheidaanduiding,
        # "beschrijving": "TODO",
    }

    informatieobject = client.create("enkelvoudiginformatieobject", data)
    return informatieobject


def relate_document(zaak_url: str, document_url: str) -> dict:
    client = Service.get_client(zaak_url)
    data = {"zaak": zaak_url, "informatieobject": document_url}

    zio = client.create("zaakinformatieobject", data)
    return zio
