from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from ..contrib.generic_json.plugin import GenericJSONRegistration
from ..contrib.microsoft_graph.plugin import MSGraphRegistration
from ..contrib.objects_api.plugin import ObjectsAPIRegistration
from ..contrib.stuf_zds.plugin import StufZDSRegistration
from ..contrib.zgw_apis.plugin import ZGWRegistration


class VendorHintTests(SimpleTestCase):
    def test_generic_json_uses_service_api_root(self):
        service = SimpleNamespace(api_root="https://json.example/api/")

        self.assertEqual(
            GenericJSONRegistration("generic-json").get_vendor_hint(
                {"service": service}
            ),
            "https://json.example/api/",
        )

    def test_objects_api_uses_objects_service_api_root(self):
        group = SimpleNamespace(
            objects_service=SimpleNamespace(api_root="https://objects.example/api/")
        )

        self.assertEqual(
            ObjectsAPIRegistration("objects-api").get_vendor_hint(
                {"objects_api_group": group}
            ),
            "https://objects.example/api/",
        )

    def test_zgw_uses_zaken_service_api_root(self):
        group = SimpleNamespace(
            zrc_service=SimpleNamespace(api_root="https://zaken.example/api/")
        )

        self.assertEqual(
            ZGWRegistration("zgw").get_vendor_hint({"zgw_api_group": group}),
            "https://zaken.example/api/",
        )

    @patch("stuf.stuf_zds.models.StufZDSConfig.get_solo")
    def test_stuf_zds_uses_soap_endpoint(self, get_solo):
        get_solo.return_value = SimpleNamespace(
            service=SimpleNamespace(
                soap_service=SimpleNamespace(url="https://soap.example/zds")
            )
        )

        self.assertEqual(
            StufZDSRegistration("stuf-zds").get_vendor_hint({}),
            "https://soap.example/zds",
        )

    def test_microsoft_graph_uses_graph_api_root(self):
        self.assertEqual(
            MSGraphRegistration("microsoft-graph").get_vendor_hint({}),
            "https://graph.microsoft.com/v1.0",
        )

    @patch("zgw_consumers.models.Service.objects.filter")
    def test_generic_json_with_pk_from_db(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            api_root="https://json.example/api/"
        )

        self.assertEqual(
            GenericJSONRegistration("generic-json").get_vendor_hint({"service": 1}),
            "https://json.example/api/",
        )
        self.assertIsNone(GenericJSONRegistration("generic-json").get_vendor_hint({}))

    @patch("openforms.contrib.objects_api.models.ObjectsAPIGroupConfig.objects.filter")
    def test_objects_api_with_pk_from_db(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            objects_service=SimpleNamespace(api_root="https://objects.example/api/")
        )

        self.assertEqual(
            ObjectsAPIRegistration("objects-api").get_vendor_hint(
                {"objects_api_group": 1}
            ),
            "https://objects.example/api/",
        )
        self.assertIsNone(ObjectsAPIRegistration("objects-api").get_vendor_hint({}))

    @patch(
        "openforms.registrations.contrib.zgw_apis.models.ZGWApiGroupConfig.objects.filter"
    )
    def test_zgw_with_pk_from_db(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            zrc_service=SimpleNamespace(api_root="https://zaken.example/api/")
        )

        self.assertEqual(
            ZGWRegistration("zgw").get_vendor_hint({"zgw_api_group": 1}),
            "https://zaken.example/api/",
        )
        self.assertIsNone(ZGWRegistration("zgw").get_vendor_hint({}))
