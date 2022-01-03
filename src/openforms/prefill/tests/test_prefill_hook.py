from copy import deepcopy

from django.test import TransactionTestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.tests.factories import SubmissionFactory

from .. import apply_prefill
from ..contrib.demo.plugin import DemoPrefill
from ..registry import Registry

register = Registry()

register("demo")(DemoPrefill)

CONFIGURATION = {
    "display": "form",
    "components": [
        {
            "id": "e4ty7zs",
            "key": "voornamen",
            "mask": False,
            "type": "textfield",
            "input": True,
            "label": "Voornamen",
            "hidden": False,
            "prefix": "",
            "suffix": "",
            "unique": False,
            "widget": {"type": "input"},
            "dbIndex": False,
            "overlay": {"top": "", "left": "", "style": "", "width": "", "height": ""},
            "prefill": {
                "plugin": "demo",
                "attribute": "random_string",
            },
            "tooltip": "",
            "disabled": False,
            "multiple": False,
            "redrawOn": "",
            "tabindex": "",
            "validate": {
                "custom": "",
                "unique": False,
                "pattern": "",
                "multiple": False,
                "required": False,
                "maxLength": "",
                "minLength": "",
                "customPrivate": False,
                "strictDateValidation": False,
            },
            "autofocus": False,
            "encrypted": False,
            "hideLabel": False,
            "inputMask": "",
            "inputType": "text",
            "modalEdit": False,
            "protected": False,
            "refreshOn": "",
            "tableView": True,
            "attributes": {},
            "errorLabel": "",
            "persistent": True,
            "properties": {},
            "spellcheck": True,
            "validateOn": "change",
            "clearOnHide": True,
            "conditional": {"eq": "", "show": None, "when": None},
            "customClass": "",
            "description": "",
            "inputFormat": "plain",
            "placeholder": "",
            "showInEmail": False,
            "defaultValue": None,
            "dataGridLabel": False,
            "labelPosition": "top",
            "showCharCount": False,
            "showWordCount": False,
            "calculateValue": "",
            "ca lculateServer": False,
            "allowMultipleMasks": False,
            "customDefaultValue": "",
            "allowCalculateOverride": False,
        }
    ],
}


class PrefillHookTests(TransactionTestCase):
    def setUp(self):
        super().setUp()

        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {}
        config.save()

    def test_applying_prefill_plugins(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)

    def test_complex_components(self):
        complex_configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e1a2cv9",
                    "key": "fieldset",
                    "type": "fieldset",
                    "components": CONFIGURATION["components"],
                },
            ],
        }
        form_step = FormStepFactory.create(
            form_definition__configuration=complex_configuration
        )
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        fieldset = new_configuration["components"][0]
        self.assertNotIn("defaultValue", fieldset)

        field = fieldset["components"][0]
        self.assertIn("prefill", field)
        self.assertIn("defaultValue", field)
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)

    def test_prefill_no_result_and_default_value_set(self):
        config = deepcopy(CONFIGURATION)
        config["components"][0]["defaultValue"] = "some-default"
        form_step = FormStepFactory.create(form_definition__configuration=config)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()

        @register("demo")
        class NoOp(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                return {}

        new_configuration = apply_prefill(
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertEqual(field["defaultValue"], "some-default")

    def tests_no_prefill_configured(self):
        config = deepcopy(CONFIGURATION)
        config["components"][0]["prefill"] = {"plugin": "", "attribute": ""}
        form_step = FormStepFactory.create(form_definition__configuration=config)
        submission = SubmissionFactory.create(form=form_step.form)

        try:
            apply_prefill(
                configuration=form_step.form_definition.configuration,
                submission=submission,
                register=register,
            )
        except Exception:
            self.fail("Pre-fill can't handle empty/no plugins")

    def test_applying_prefill_plugins_not_enabled(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {"prefill": {"demo": {"enabled": False}}}
        config.save()

        with self.assertRaises(PluginNotEnabled):
            apply_prefill(
                configuration=form_step.form_definition.configuration,
                submission=submission,
                register=register,
            )
