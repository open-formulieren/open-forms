from logging import exception
from django.test import TestCase
# from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from .models import ObjectsAPIConfig
from ..plugin import ObjectsAPIRegistration as oar


class OrcPluginTesterTest(TestCase):

    def setUp(self):
        # self.plugin = ZGWRegistration("zgw")
        self.oac = ObjectsAPIConfig.get_solo()
        drc_client = self.oac.drc_service.build_client()
        orc_client = self.oac.objects_service.build_client()

        self.lients = [{'type': 'object', 'client': orc_client},
                   {'type': 'document', 'client': drc_client},
                ]

    def test_zgw_plugin(self):
        self.assertEqual(self.documents_client.base_url, 'https://documenten.nl/api/v1/')
        self.assertEqual(self.orc_client.base_url, 'https://test.openzaak.nl/objecten/api/v1/')

        for i, client in enumerate(self.clients):
            try:
                client['client'].retrieve(client['type'], client['client'].base_url)
                try:
                    self.assertEqual(oar.test_config(), [])
                except Exception as e:
                    self.assertEqual(oar.test_config()[i]['error'], str(e))
            except Exception as e:
                pass