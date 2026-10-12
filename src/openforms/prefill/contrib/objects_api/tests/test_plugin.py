import uuid

from django.test import TestCase

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory

from ..plugin import ObjectsAPIPrefill


class ObjectsAPIPrefillPluginTestCase(TestCase):
    def test_plugin_configuration_context_api_groups(self):
        plugin = ObjectsAPIPrefill("objects_api")
        group1 = ObjectsAPIGroupConfigFactory.create(name="Foo")
        group2 = ObjectsAPIGroupConfigFactory.create(name="Bar")

        expected = {
            "api_groups": [
                [
                    group1.identifier,
                    "Foo",
                ],
                [
                    group2.identifier,
                    "Bar",
                ],
            ]
        }

        self.assertEqual(plugin.configuration_context(), expected)

    def test_get_vendor_hint(self):
        plugin = ObjectsAPIPrefill("objects_api")
        group = ObjectsAPIGroupConfigFactory.create(
            objects_service__api_root="https://objects.example/api/"
        )
        serializer = plugin.options(
            data={
                "objects_api_group": group.identifier,
                "objecttype_uuid": uuid.uuid4(),
                "objecttype_version": 3,
                "skip_ownership_check": True,
                "auth_attribute_path": [],
                "variables_mapping": [],
            }
        )
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://objects.example/api/",
        )
