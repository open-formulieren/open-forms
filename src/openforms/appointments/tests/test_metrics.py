from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

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
            3, is_appointment_form=True, active=True, deleted_=False
        )
        FormFactory.create(is_appointment_form=True, active=True, deleted_=True)
        FormFactory.create(is_appointment_form=True, active=False, deleted_=False)
        FormFactory.create(is_appointment_form=False, active=True, deleted_=False)

        result = {
            plugin.identifier: amount
            for plugin, amount in register.report_plugin_usage()
        }

        self.assertEqual(result["demo"], 3)

        for key, value in result.items():
            if key == "demo":
                continue
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)

    def test_appointment_forms_present_but_no_plugin_configured(self):
        config = AppointmentsConfig.get_solo()
        config.plugin = ""
        config.save()
        self.addCleanup(AppointmentsConfig.clear_cache)
        FormFactory.create(is_appointment_form=True, active=True, deleted_=False)

        result = {
            plugin.identifier: amount
            for plugin, amount in register.report_plugin_usage()
        }

        for key, value in result.items():
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)

    def test_plugin_configured_but_no_appointment_forms_present(self):
        result = {
            plugin.identifier: amount
            for plugin, amount in register.report_plugin_usage()
        }

        for key, value in result.items():
            with self.subTest(plugin=key):
                self.assertEqual(value, 0)
