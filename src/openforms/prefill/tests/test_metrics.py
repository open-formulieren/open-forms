from django.test import TestCase

from openforms.forms.tests.factories import FormFactory, FormVariableFactory

from .utils import get_test_register

register = get_test_register()  # only has the demo plugin


CONFIGURATION = {
    "display": "form",
    "components": [
        {
            "key": "voornamen",
            "type": "textfield",
            "label": "Voornamen",
            "prefill": {
                "plugin": "demo",
                "attribute": "random_string",
            },
            "multiple": False,
        },
        {
            "key": "age",
            "type": "number",
            "label": "Age",
            "prefill": {
                "plugin": "demo",
                "attribute": "random_number",
            },
            "multiple": False,
        },
    ],
}


class ReportPluginUsageTests(TestCase):
    def test_report_counts_from_live_forms(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
        )
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
            deleted_=True,
        )
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
            active=False,
        )

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo"][0], 2)
        self.assertEqual(result["demo"][1], {})

    def test_includes_user_defined_variables(self):
        FormVariableFactory.create(
            user_defined=True, prefill_plugin="demo", prefill_attribute="random_number"
        )
        FormVariableFactory.create(
            form__active=False,
            user_defined=True,
            prefill_plugin="demo",
            prefill_attribute="random_number",
        )
        FormVariableFactory.create(
            form__deleted_=True,
            user_defined=True,
            prefill_plugin="demo",
            prefill_attribute="random_number",
        )

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo"][0], 1)
        self.assertEqual(result["demo"][1], {})

    def test_unregistered_prefill_plugin_is_ignored(self):
        FormVariableFactory.create(
            user_defined=True,
            prefill_plugin="non_existent_plugin",
            prefill_attribute="random_number",
        )

        result = {
            plugin.identifier: (count, tags)
            for plugin, count, tags in register.report_plugin_usage()
        }

        self.assertEqual(result["demo"][0], 0)
        self.assertEqual(result["demo"][1], {})
        self.assertNotIn("non_existent_plugin", result)
