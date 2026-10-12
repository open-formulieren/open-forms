from django.test import TestCase

from ..plugin import ZGWRegistration
from .factories import ZGWApiGroupConfigFactory


class ZGWVendorHintTests(TestCase):
    def test_get_vendor_hint_uses_zaken_service_api_root(self):
        group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken.example/api/"
        )
        plugin = ZGWRegistration("zgw")
        serializer = plugin.configuration_options(
            data={
                "zgw_api_group": group.pk,
                "catalogue": {"domain": "", "rsin": ""},
                "case_type_identification": "TEST",
                "document_type_description": "Test document",
            },
            context={"validate_business_logic": False},
        )
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://zaken.example/api/",
        )
