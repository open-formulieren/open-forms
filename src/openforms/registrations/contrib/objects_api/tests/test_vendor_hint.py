import uuid

from django.test import TestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory

from ..plugin import ObjectsAPIRegistration


class ObjectsAPIVendorHintTests(TestCase):
    def test_get_vendor_hint_uses_objects_service_api_root(self):
        group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objects.example/api/"
        )
        plugin = ObjectsAPIRegistration("objects-api")
        serializer = plugin.configuration_options(
            data={
                "objects_api_group": group.identifier,
                "version": 2,
                "objecttype": str(uuid.uuid4()),
                "objecttype_version": 1,
                "variables_mapping": [],
            },
            context={"validate_business_logic": False},
        )
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://objects.example/api/",
        )
