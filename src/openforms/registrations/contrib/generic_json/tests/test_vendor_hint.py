from django.test import TestCase

from zgw_consumers.constants import APITypes
from zgw_consumers.test.factories import ServiceFactory

from ..plugin import GenericJSONRegistration


class GenericJSONVendorHintTests(TestCase):
    def test_get_vendor_hint_uses_service_api_root(self):
        service = ServiceFactory.create(
            api_root="https://json.example/api/",
            api_type=APITypes.orc,
        )
        plugin = GenericJSONRegistration("generic-json")
        serializer = plugin.configuration_options(
            data={
                "service": service.pk,
                "path": "",
                "variables": ["now"],
                "fixed_metadata_variables": [],
                "additional_metadata_variables": [],
                "transform_to_list": [],
                "use_empty_string_for_empty_datelike_variables": False,
            }
        )
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://json.example/api/",
        )
