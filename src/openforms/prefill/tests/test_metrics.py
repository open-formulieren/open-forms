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
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"demo": 2})

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
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"demo": 1})
