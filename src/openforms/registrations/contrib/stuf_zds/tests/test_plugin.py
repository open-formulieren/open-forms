from django.test import TestCase
from ..client import StufZDSClient
from ..models import StufZDSConfig
from stuf.models import SoapService
import uuid
from django.template import loader
import requests_mock
from privates.test import temp_private_root
from stuf.tests.factories import SoapServiceFactory


def load_mock(name, context=None):
    return loader.render_to_string(
        f"stuf_zds/soap/response-mock/{name}", context
    ).encode("utf8")

@temp_private_root()
@requests_mock.Mocker()
class StufPluginTesterTest(TestCase):

    def setUp(self):
        # self.service = SoapService()
        self.service = SoapServiceFactory(
            zender_organisatie="ZenOrg",
            zender_applicatie="ZenApp",
            zender_administratie="ZenAdmin",
            zender_gebruiker="ZenUser",
            ontvanger_organisatie="OntOrg",
            ontvanger_applicatie="OntApp",
            ontvanger_administratie="OntAdmin",
            ontvanger_gebruiker="OntUser",
        )

        self.options = {
            "gemeentecode": "1234",
            "omschrijving": "my-form",
            "zds_zaaktype_code": "zt-code",
            "zds_zaaktype_omschrijving": "zt-omschrijving",
            "zds_zaaktype_status_code": "zt-st-code",
            "zds_zaaktype_status_omschrijving": "zt-st-omschrijving",
            "zds_documenttype_omschrijving": "dt-omschrijving",
            "referentienummer": str(uuid.uuid4()),
        }
        self.config = StufZDSConfig.get_solo()
        self.config.apply_defaults_to(self.options)
        self.client = self.config.get_client(self.options)
        # self.client = StufZDSClient(self.service, self.options)

    def test_stuf_plugin(self, m):
        m.post(
            self.service.url,
            content=load_mock(
                "genereerDocumentIdentificatie.xml", {"document_identificatie": "tester"}
            ),
        )

        identificatie = self.client.create_document_identificatie()
        self.assertEqual(identificatie, "tester")