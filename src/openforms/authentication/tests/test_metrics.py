from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

from ..contrib.demo.plugin import DemoBSNAuthentication, DemoKVKAuthentication
from ..registry import Registry

register = Registry()
register("bsn")(DemoBSNAuthentication)
register("kvk")(DemoKVKAuthentication)


class ReportPluginUsageTests(TestCase):
    def test_live_form_counts_reported(self):
        FormFactory.create(authentication_backend="bsn")
        FormFactory.create(authentication_backend="bsn")

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["bsn"][0], 2)
        self.assertEqual(result["kvk"][0], 0)
        self.assertEqual(result["bsn"][1], {})
        self.assertEqual(result["kvk"][1], {})

    def test_deleted_or_deactivated_forms_are_ignored(self):
        FormFactory.create(authentication_backend="bsn", active=False, deleted_=False)
        FormFactory.create(authentication_backend="kvk", active=True, deleted_=True)

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["bsn"][0], 0)
        self.assertEqual(result["kvk"][0], 0)
        self.assertEqual(result["bsn"][1], {})
        self.assertEqual(result["kvk"][1], {})

    def test_unregistered_auth_plugin_is_ignored(self):
        FormFactory.create(authentication_backend="missing_auth_plugin")

        results = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(results["bsn"][0], 0)
        self.assertEqual(results["kvk"][0], 0)
        self.assertNotIn("missing_auth_plugin", results)

    def test_vendor_hint_included_in_metrics(self):
        class DummyPlugin(DemoBSNAuthentication):
            def get_vendor_hint(self, options):
                return "https://idp.example.com/metadata"

        custom_register = Registry()
        custom_register("dummy")(DummyPlugin)
        FormFactory.create(authentication_backend="dummy")

        reports = list(custom_register.report_plugin_usage())
        self.assertEqual(len(reports), 1)
        _plugin, count, tags = reports[0]
        self.assertEqual(count, 1)
        self.assertEqual(
            tags,
            {"openforms.plugin.vendor_hint": "https://idp.example.com/metadata"},
        )
