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

        self.clients = [{'type': 'object', 'client': orc_client},
                        {'type': 'document', 'client': drc_client},
                        ]

    def test_zgw_plugin(self):

        for client in self.clients:
            try:
                self.assertEqual(client['client'].retrieve(client['type'], client['client'].base_url), True)
            except Exception as e:
                self.assertEqual(client['client'].retrieve(client['type'], client['client'].base_url), [str(e)])
