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

    def test_vendor_hint_included_in_metrics(self):
        from openforms.forms.tests.factories import FormRegistrationBackendFactory

        class DummyPlugin(DemoRegistration):
            def get_vendor_hint(self, options):
                return options.get("url")

        custom_register = Registry()
        custom_register("dummy")(DummyPlugin)
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            backend="dummy",
            options={"url": "https://api.example.com"},
        )

        reports = list(custom_register.report_plugin_usage())
        self.assertEqual(len(reports), 1)
        _plugin, count, tags = reports[0]
        self.assertEqual(count, 1)
        self.assertEqual(
            tags, {"openforms.plugin.vendor_hint": "https://api.example.com"}
        )
