from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

from ..contrib.demo.plugin import DemoRegistration
from ..registry import Registry

register = Registry()
register("demo1")(DemoRegistration)
register("demo2")(DemoRegistration)


class ReportPluginUsageTests(TestCase):
    def test_live_form_counts_reported(self):
        FormFactory.create(registration_backend="demo1")
        FormFactory.create(registration_backend="demo1")

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo1"][0], 2)
        self.assertEqual(result["demo2"][0], 0)
        self.assertEqual(result["demo1"][1], {})
        self.assertEqual(result["demo2"][1], {})

    def test_deleted_or_deactivated_forms_are_ignored(self):
        FormFactory.create(registration_backend="demo1", active=False, deleted_=False)
        FormFactory.create(registration_backend="demo2", active=True, deleted_=True)

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo1"][0], 0)
        self.assertEqual(result["demo2"][0], 0)
        self.assertEqual(result["demo1"][1], {})
        self.assertEqual(result["demo2"][1], {})

    def test_unregistered_registration_plugin_is_ignored(self):
        FormFactory.create(registration_backend="missing_registration_plugin")

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo1"][0], 0)
        self.assertEqual(result["demo2"][0], 0)
        self.assertNotIn("missing_registration_plugin", result)
