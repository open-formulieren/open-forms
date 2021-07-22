import uuid

from django.core.management import BaseCommand

from openforms.registrations.contrib.stuf_zds.client import StufZDSClient
from stuf.models import SoapService


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("create", action="store", choices=("zaak", "document"))
        parser.add_argument(
            "initiator",
            action="store",
            choices=("bsn", "nnp", "vestiging", "anon"),
            nargs="?",
            default="anon",
        )
        parser.add_argument(
            "--url",
            action="store",
            type=str,
            help="STP test URL",
            nargs="?",
            default="http://stuftestplatform.nl:7080/opentunnel/00000000000000000000041/51037857/AllTypes",
        )
        # add auth like user/password and certificates

    def handle(self, *args, **options):
        service = SoapService()
        service.url = options["url"]
        service.ontvanger_organisatie = "ORG"
        service.ontvanger_applicatie = "TTA"
        service.zender_organisatie = "KING"
        service.zender_applicatie = "TTA"

        client_options = {
            "gemeentecode": "1234",
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving": "dt-omschrijving",
            "referentienummer": str(uuid.uuid4()),
        }

        client = StufZDSClient(service, client_options)

        if options["create"] == "zaak":
            data = dict()
            initiator = options["initiator"]
            if initiator == "bsn":
                data["bsn"] = "111222333"
            elif initiator == "nnp":
                data["nnp_id"] = "111222333"
            elif initiator == "vestiging":
                data["vestigings_nummer"] = "000111222333"
            elif initiator == "anon":
                data["anp_id"] = "12345678901234567"

            zaak_id = client.create_zaak_identificatie()
            client.create_zaak(zaak_id, data)

        elif options["create"] == "document":
            data = {
                "test": 123,
            }
            zaak_id = "0000c765c781-cedc-4c17-bc25-6a80ec24de07"
            doc_id = client.create_document_identificatie()
            client.create_zaak_document(zaak_id, doc_id, data)
