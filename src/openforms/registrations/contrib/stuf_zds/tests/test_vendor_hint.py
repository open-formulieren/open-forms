from unittest.mock import patch

from django.test import SimpleTestCase

from stuf.stuf_zds.models import StufZDSConfig
from stuf.tests.factories import StufServiceFactory

from ..plugin import PLUGIN_IDENTIFIER, StufZDSRegistration


class StufZDSVendorHintTests(SimpleTestCase):
    @patch("stuf.stuf_zds.models.StufZDSConfig.get_solo")
    def test_get_vendor_hint_uses_soap_endpoint(self, get_solo):
        get_solo.return_value = StufZDSConfig(
            service=StufServiceFactory.build(
                soap_service__url="https://soap.example/zds"
            )
        )
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)
        serializer = plugin.configuration_options(
            data={
                "zds_zaaktype_code": "Z01",
                "zds_documenttype_omschrijving_inzending": "",
            }
        )
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://soap.example/zds",
        )
