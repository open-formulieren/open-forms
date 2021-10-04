from django.test import TestCase
from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from ..plugin import ZGWRegistration as zwgr
from .factories import ZgwConfigFactory


class ZgwPluginTesterTest(TestCase):

    def setUp(self):
        self.zgw = ZgwConfig.get_solo()
        self.zaken_client = self.zgw.zrc_service.build_client()
        self.documents_client = self.zgw.drc_service.build_client()
        self.zaaktypen_client = self.zgw.ztc_service.build_client()

        self.clients = [{'type': 'zaak', 'client': self.zaken_client},
                   {'type': 'document', 'client': self.documents_client},
                   {'type': 'zaaktype', 'client': self.zaaktypen_client}]

    def test_zgw_plugin(self):
        self.assertEqual(self.zaken_client.base_url, 'https://zaken.nl/api/v1/')
        self.assertEqual(self.documents_client.base_url, 'https://documenten.nl/api/v1/')
        self.assertEqual(self.zaaktypen_client.base_url, 'https://catalogus.nl/api/v1/')

        for i, client in enumerate(self.clients):
            try:
                client['client'].retrieve(client['type'], client['client'].base_url)
                try:
                    self.assertEqual(zwgr.test_config(), [])
                except Exception as e:
                    self.assertEqual(zwgr.test_config()[i]['error'], str(e))
            except Exception as e:
                pass

