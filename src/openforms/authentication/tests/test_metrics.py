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
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"bsn": 2, "kvk": 0})

    def test_deleted_or_deactivated_forms_are_ignored(self):
        FormFactory.create(authentication_backend="bsn", active=False, deleted_=False)
        FormFactory.create(authentication_backend="kvk", active=True, deleted_=True)

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"bsn": 0, "kvk": 0})
