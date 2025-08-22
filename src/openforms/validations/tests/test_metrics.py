from django.test import TestCase

from openforms.forms.tests.factories import FormDefinitionFactory, FormFactory

from ..base import BasePlugin
from ..registry import Registry

register = Registry()


@register("demo")
class DummyValidator(BasePlugin[str | int | float]):
    def __call__(self, value, submission):
        pass


CONFIGURATION = {
    "type": "form",
    "components": [
        {
            "type": "textfield",
            "key": "textfield1",
            "label": "Text 1",
        },
        {
            "type": "fieldset",
            "key": "fieldset1",
            "label": "",
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield2",
                    "label": "Text 2",
                    "validate": {"required": True},
                },
                {
                    "type": "textfield",
                    "key": "textfield3",
                    "label": "Text 3",
                    "validate": {"required": False, "plugins": ["demo"]},
                },
            ],
        },
        {
            "type": "number",
            "key": "number1",
            "label": "Number 1",
            "validate": {"required": False, "plugins": ["demo"]},
        },
    ],
}


class ReportPluginUsageTests(TestCase):
    def test_live_form_counts_reported(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
        )
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
            active=False,
        )
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
            deleted_=True,
        )

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"demo": 2})

    def test_reused_form_definition_counted_multiple_times(self):
        fd = FormDefinitionFactory.create(is_reusable=True, configuration=CONFIGURATION)
        FormFactory.create_batch(
            2, generate_minimal_setup=True, formstep__form_definition=fd
        )

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"demo": 4})
