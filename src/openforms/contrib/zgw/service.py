from datetime import date

from .models import ZgwConfig


def create_zaak():
    config = ZgwConfig.get_solo()
    client = config.zrc_service.build_client()
    today = date.today().isoformat()
    data = {
        "zaaktype": config.zaaktype,
        "bronorganisatie": config.organisatie_rsin,
        "verantwoordelijkeOrganisatie": config.organisatie_rsin,
        "registratiedatum": today,
        "startdatum": today,
    }

    zaak = client.create("zaak", data)
    return zaak


def create_document(body):
    config = ZgwConfig.get_solo()
    client = config.drc_service.build_client()


def relate_document(zaak_url, document_url):
    pass
