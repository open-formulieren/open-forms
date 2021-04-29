import json
from base64 import b64encode
from datetime import date

from django.core.serializers.json import DjangoJSONEncoder
from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_rest.models import ZgwConfig


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
        # "omschrijving": "TODO",
        # "toelichting": "TODO",
        "vertrouwelijkheidaanduiding": options["vertrouwelijkheidaanduiding"],
        # "betalingsindicatie": "nvt",
        # "selectielijstklasse": "TODO",
        # "archiefnominatie": "vernietigen",
    }

    zaak = client.create("zaak", data)
    return zaak


def create_document(name: str, body: dict, options: dict) -> dict:
    config = ZgwConfig.get_solo()
    client = config.drc_service.build_client()
    today = date.today().isoformat()
    # TODO is a json document what we want?
    base64_body = b64encode(json.dumps(body, cls=DjangoJSONEncoder).encode()).decode()
    data = {
        "informatieobjecttype": options['informatieobjecttype'],
        "bronorganisatie": options['organisatie_rsin'],
        "creatiedatum": today,
        "titel": name,
        "auteur": "openforms",
        "taal": "nld",
        "inhoud": base64_body,
        "vertrouwelijkheidaanduiding": options['vertrouwelijkheidaanduiding'],
        # "beschrijving": "TODO",
    }

    informatieobject = client.create("enkelvoudiginformatieobject", data)
    return informatieobject


def relate_document(zaak_url: str, document_url: str) -> dict:
    client = Service.get_client(zaak_url)
    data = {"zaak": zaak_url, "informatieobject": document_url}

    zio = client.create("zaakinformatieobject", data)
    return zio
