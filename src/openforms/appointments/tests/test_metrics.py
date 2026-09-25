from django.test import TestCase

from openforms.forms.constants import FormTypeChoices
from openforms.forms.tests.factories import FormFactory
from openforms.plugins.registry import VENDOR_HINT_METRIC_LABEL

from ..models import AppointmentsConfig
from ..registry import register


class ReportPluginUsageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # use demo plugin for tests
        cls.plugin = register["demo"]

        config = AppointmentsConfig.get_solo()
        config.plugin = "demo"
        config.save()
        cls.addClassCleanup(AppointmentsConfig.clear_cache)

    def test_report_usages_equal_to_number_of_appointment_forms(self):
        FormFactory.create_batch(
            3, type=FormTypeChoices.appointment, active=True, deleted_=False
        )
        FormFactory.create(type=FormTypeChoices.appointment, active=True, deleted_=True)
        FormFactory.create(
            type=FormTypeChoices.appointment, active=False, deleted_=False
        )
        FormFactory.create(type=FormTypeChoices.regular, active=True, deleted_=False)

        result = {
            plugin.identifier: (amount, tags)
            for plugin, amount, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo"][0], 3)
        self.assertEqual(result["demo"][1], {VENDOR_HINT_METRIC_LABEL: "demo"})

        for key, (value, _tags) in result.items():
            if key == "demo":
                continue
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)

    def test_appointment_forms_present_but_no_plugin_configured(self):
        config = AppointmentsConfig.get_solo()
        config.plugin = ""
        config.save()
        self.addCleanup(AppointmentsConfig.clear_cache)
        FormFactory.create(
            type=FormTypeChoices.appointment, active=True, deleted_=False
        )

        result = {
            plugin.identifier: (amount, tags)
            for plugin, amount, tags in register.report_plugin_usage()
        }

        for key, (value, _tags) in result.items():
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)

    def test_plugin_configured_but_no_appointment_forms_present(self):
        result = {
            plugin.identifier: (amount, tags)
            for plugin, amount, tags in register.report_plugin_usage()
        }

        for key, (value, _tags) in result.items():
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)

    def test_vendor_hints_coverage(self):
        class CustomDummyPlugin:
            identifier = "plugin"

        register["plugin"] = CustomDummyPlugin

        try:
            for plugin, _amount, tags in register.report_plugin_usage():
                identifier_lower = plugin.identifier.lower()
                if "jcc" in identifier_lower:
                    self.assertEqual(tags.get(VENDOR_HINT_METRIC_LABEL), "jcc_rest")
                elif "qmatic" in identifier_lower:
                    self.assertEqual(tags.get(VENDOR_HINT_METRIC_LABEL), "qmatic")
                elif "demo" in identifier_lower:
                    self.assertEqual(tags.get(VENDOR_HINT_METRIC_LABEL), "demo")
                else:
                    self.assertEqual(
                        tags.get(VENDOR_HINT_METRIC_LABEL), plugin.identifier
                    )
        finally:
            del register["plugin"]
