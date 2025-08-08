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
