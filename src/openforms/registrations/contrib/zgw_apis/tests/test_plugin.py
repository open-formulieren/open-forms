from django.test import TestCase
from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from ..plugin import ZGWRegistration
from .factories import ZgwConfigFactory


class ZgwPluginTesterTest(TestCase):

    def setUp(self):
        self.plugin = ZGWRegistration("zgw")
        self.zgw = ZgwConfig.get_solo()
        # self.zaken_client = self.zgw.zrc_service.build_client()
        # self.documents_client = self.zgw.drc_service.build_client()
        # self.zaaktypen_client = self.zgw.ztc_service.build_client()

    def test_zgw_plugin(self):
        print('zgwppplluugggiinns', ZgwConfigFactory.drc_service)
        # retrieve_zaak = self.zaken_client.retrieve('zaak', self.zaken_client['base_url'])
        # retrieve_document = self.documents_client.retrieve('zaak', self.documents_client['base_url'])
        # retrieve_zaaktypen = self.zaaktypen_client.retrieve('zaak', self.zaaktypen_client['base_url'])

        # self.assertContains(self.zaken_client, self.zaken_client['base_url'])
        # self.assertContains(self.retrieve_document, self.retrieve_document['base_url'])
        # self.assertContains(self.retrieve_zaaktypen, self.retrieve_zaaktypen['base_url'])

        # for k, v in retrieve_zaak.items():
        #     self.assertEqual(retrieve_zaak[k], self.zaken_client['base_url']+'/'+k)

        # for k, v in retrieve_document.items():
        #     self.assertEqual(retrieve_document[k], self.documents_client['base_url']+'/'+k)

        # for k, v in retrieve_zaaktypen.items():
        #     self.assertEqual(retrieve_zaaktypen[k], self.zaaktypen_client['base_url']+'/'+k)
