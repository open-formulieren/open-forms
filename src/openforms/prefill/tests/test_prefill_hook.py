from copy import deepcopy
from unittest.mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.tests.factories import SubmissionFactory

from ...tests.utils import NOOP_CACHES
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


@override_settings(
    CACHES=NOOP_CACHES, SESSION_ENGINE="django.contrib.sessions.backends.db"
)
class PrefillHookTests(TestCase):
    def setUp(self):
        super().setUp()

        # create a dummy request with working session
        self.request = RequestFactory().get("/")
        middleware = SessionMiddleware()
        middleware.process_request(self.request)
        self.request.session.save()

    def test_applying_prefill_plugins(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            self.request,
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
            self.request,
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
            self.request,
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
                self.request,
                configuration=form_step.form_definition.configuration,
                submission=submission,
                register=register,
            )
        except Exception:
            self.fail("Pre-fill can't handle empty/no plugins")

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_applying_prefill_plugins_not_enabled(self, mock_get_solo):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"prefill": {"demo": {"enabled": False}}}
        )

        with self.assertRaises(PluginNotEnabled):
            apply_prefill(
                self.request,
                configuration=form_step.form_definition.configuration,
                submission=submission,
                register=register,
            )

    @patch("openforms.prefill.tests.test_prefill_hook.DemoPrefill.get_prefill_values")
    def test_prefill_date_isoformat(self, m_get_prefill_value):
        m_get_prefill_value.return_value = {"random_isodate": "2020-12-12"}

        configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e4ty7zs",
                    "key": "dateOfBirth",
                    "type": "date",
                    "input": True,
                    "label": "Date of Birth",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_isodate",
                    },
                    "multiple": False,
                    "defaultValue": None,
                }
            ],
        }
        form_step = FormStepFactory.create(form_definition__configuration=configuration)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            self.request,
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)
        self.assertEqual("2020-12-12", field["defaultValue"])

    @patch("openforms.prefill.tests.test_prefill_hook.DemoPrefill.get_prefill_values")
    def test_prefill_date_stufbg_format(self, m_get_prefill_value):
        m_get_prefill_value.return_value = {"random_stufbg_date": "20201212"}

        configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e4ty7zs",
                    "key": "dateOfBirth",
                    "type": "date",
                    "input": True,
                    "label": "Date of Birth",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "random_stufbg_date",
                    },
                    "multiple": False,
                    "defaultValue": None,
                }
            ],
        }
        form_step = FormStepFactory.create(form_definition__configuration=configuration)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            self.request,
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)
        self.assertEqual("2020-12-12", field["defaultValue"])

    @patch("openforms.prefill.tests.test_prefill_hook.DemoPrefill.get_prefill_values")
    def test_prefill_invalid_date(self, m_get_prefill_value):
        m_get_prefill_value.return_value = {"invalid_date": "123456789"}

        configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e4ty7zs",
                    "key": "dateOfBirth",
                    "type": "date",
                    "input": True,
                    "label": "Date of Birth",
                    "prefill": {
                        "plugin": "demo",
                        "attribute": "invalid_date",
                    },
                    "multiple": False,
                    "defaultValue": None,
                }
            ],
        }
        form_step = FormStepFactory.create(form_definition__configuration=configuration)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            self.request,
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)
        self.assertEqual("", field["defaultValue"])

    def test_apply_prefill_caches_values(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()
        counter = 0

        @register("demo")
        class CountPlugin(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                nonlocal counter
                counter += 1
                return {a: "foo" for a in attributes}

        # first call increases counter
        new_configuration = apply_prefill(
            self.request,
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )
        self.assertEqual(counter, 1)

        field = new_configuration["components"][0]
        self.assertEqual(field["defaultValue"], "foo")

        # second call hits cache
        new_configuration = apply_prefill(
            self.request,
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )
        # still just one
        self.assertEqual(counter, 1)

        field = new_configuration["components"][0]
        self.assertEqual(field["defaultValue"], "foo")

    def test_apply_prefill_caches_values_across_steps_and_plugins(self):
        """
        similar to basic test except we check with multiple plugins, step and recurring prefills
        """
        step_one_configuration = {
            "display": "form",
            "components": [
                {
                    "id": "one1",
                    "type": "text",
                    "prefill": {
                        "plugin": "alpha",
                        "attribute": "alpha_one",
                    },
                    "defaultValue": None,
                },
                {
                    "id": "one2",
                    "type": "text",
                    "prefill": {
                        "plugin": "bravo",
                        "attribute": "bravo_one",
                    },
                    "defaultValue": None,
                },
            ],
        }

        # in step two we use same plugins but different attributes
        step_two_configuration = {
            "display": "form",
            "components": [
                {
                    "id": "two1",
                    "type": "text",
                    "prefill": {
                        "plugin": "alpha",
                        "attribute": "alpha_two",
                    },
                    "defaultValue": None,
                },
                {
                    "id": "two2",
                    "type": "text",
                    "prefill": {
                        "plugin": "bravo",
                        "attribute": "bravo_two",
                    },
                    "defaultValue": None,
                },
                # also add a recurring prefill from step one
                {
                    "id": "two2",
                    "type": "text",
                    "prefill": {
                        "plugin": "alpha",
                        "attribute": "alpha_one",
                    },
                    "defaultValue": None,
                },
            ],
        }

        form = FormFactory.create()
        form_step_one = FormStepFactory.create(
            form=form, form_definition__configuration=step_one_configuration
        )
        form_step_two = FormStepFactory.create(
            form=form, form_definition__configuration=step_two_configuration
        )
        submission = SubmissionFactory.create(form=form)

        register = Registry()

        alpha_fetch_log = list()
        bravo_fetch_log = list()

        @register("alpha")
        class AlphaPlugin(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                for a in attributes:
                    alpha_fetch_log.append(a)
                return {a: f"{a}_value" for a in attributes}

        @register("bravo")
        class BravoPlugin(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                for a in attributes:
                    bravo_fetch_log.append(a)
                return {a: f"{a}_value" for a in attributes}

        # prefill step one
        new_configuration_one = apply_prefill(
            self.request,
            configuration=form_step_one.form_definition.configuration,
            submission=submission,
            register=register,
        )
        # attributes logged as expected
        self.assertEqual(alpha_fetch_log, ["alpha_one"])
        self.assertEqual(bravo_fetch_log, ["bravo_one"])

        # prefill step one again
        new_configuration_one = apply_prefill(
            self.request,
            configuration=form_step_one.form_definition.configuration,
            submission=submission,
            register=register,
        )
        # no change
        self.assertEqual(alpha_fetch_log, ["alpha_one"])
        self.assertEqual(bravo_fetch_log, ["bravo_one"])

        # prefill step two
        new_configuration_two = apply_prefill(
            self.request,
            configuration=form_step_two.form_definition.configuration,
            submission=submission,
            register=register,
        )

        # step two attributes added as expected, but no repeat of recurring attributes from step one
        self.assertEqual(alpha_fetch_log, ["alpha_one", "alpha_two"])
        self.assertEqual(bravo_fetch_log, ["bravo_one", "bravo_two"])

        # call both again, lets do in different order
        new_configuration_two = apply_prefill(
            self.request,
            configuration=form_step_two.form_definition.configuration,
            submission=submission,
            register=register,
        )
        new_configuration_one = apply_prefill(
            self.request,
            configuration=form_step_one.form_definition.configuration,
            submission=submission,
            register=register,
        )

        # no change
        self.assertEqual(alpha_fetch_log, ["alpha_one", "alpha_two"])
        self.assertEqual(bravo_fetch_log, ["bravo_one", "bravo_two"])

        # check values
        field = new_configuration_one["components"][0]
        self.assertEqual(field["defaultValue"], "alpha_one_value")

        field = new_configuration_one["components"][1]
        self.assertEqual(field["defaultValue"], "bravo_one_value")

        field = new_configuration_two["components"][0]
        self.assertEqual(field["defaultValue"], "alpha_two_value")

        field = new_configuration_two["components"][1]
        self.assertEqual(field["defaultValue"], "bravo_two_value")

        # (recurring from step one)
        field = new_configuration_two["components"][2]
        self.assertEqual(field["defaultValue"], "alpha_one_value")
