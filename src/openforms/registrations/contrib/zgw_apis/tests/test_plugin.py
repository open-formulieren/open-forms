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
                        {'type': 'document', 'client': self.drc_client},
                        {'type': 'zaaktype', 'client': self.drc_clzaaktypen_clientient},
                        ]

    def test_zgw_plugin(self):

        for client in self.clients:
            try:
                self.assertEqual(client['client'].retrieve(client['type'], client['client'].base_url), True)
            except Exception as e:
                self.assertEqual(client['client'].retrieve(client['type'], client['client'].base_url), [str(e)])
