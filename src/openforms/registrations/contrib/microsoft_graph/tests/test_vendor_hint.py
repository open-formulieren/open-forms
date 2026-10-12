from django.test import SimpleTestCase

from ..plugin import MSGraphRegistration


class MSGraphVendorHintTests(SimpleTestCase):
    def test_get_vendor_hint_uses_graph_api_root(self):
        plugin = MSGraphRegistration("microsoft-graph")
        serializer = plugin.configuration_options(data={})
        serializer.is_valid(raise_exception=True)

        self.assertEqual(
            plugin.get_vendor_hint(serializer.validated_data),
            "https://graph.microsoft.com/v1.0",
        )
