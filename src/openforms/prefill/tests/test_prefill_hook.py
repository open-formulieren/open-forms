import logging
from copy import deepcopy
from unittest.mock import patch

from django.template.defaultfilters import escape_filter
from django.test import TransactionTestCase
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from openforms.config.models import GlobalConfiguration
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.logging.models import TimelineLogProxy
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from .. import inject_prefill, prefill_variables
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


def apply_prefill(configuration: dict, submission: "Submission", register=None) -> dict:
    # apply_prefill used to be a public function in openforms.prefill, which became
    # obsolete after introducing the variables feature and has therefore been removed.
    # The prefill is now calculated on submission start and stored in the variable values
    # in the DB, and then later on again injected in the configuration.
    #
    # This function wraps around the new behaviour so that we can keep the existing
    # tests to prevent regressions.

    # simulate the submission start which causes the prefill data to be persisted. We
    # refresh the submission instance manually to avoid polluted python state.
    configuration = deepcopy(configuration)
    _submission = Submission.objects.get(pk=submission.pk)
    prefill_variables(_submission, register=register)
    inject_prefill(FormioConfigurationWrapper(configuration), _submission)
    return configuration


class PrefillHookTests(TransactionTestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        TimelineLogProxy.objects.all().delete()

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
        def config_factory():
            components = deepcopy(CONFIGURATION["components"])
            for index, comp in enumerate(components):
                comp["id"] = get_random_string(length=7)
                comp["key"] = comp["key"] + get_random_string(length=4)
            return components

        complex_configuration = {
            "display": "form",
            "components": [
                {
                    "id": "e1a2cv9",
                    "key": "fieldset",
                    "type": "fieldset",
                    "components": config_factory(),
                },
                {
                    "key": "columns",
                    "type": "columns",
                    "columns": [
                        {
                            "size": 6,
                            "components": config_factory(),
                        },
                        {
                            "size": 6,
                            "components": config_factory(),
                        },
                    ],
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

        column1, column2 = new_configuration["components"][1]["columns"]
        self.assertNotIn("defaultValue", column1)
        self.assertNotIn("defaultValue", column2)
        col_field1, col_field2 = column1["components"][0], column2["components"][0]

        self.assertIn("prefill", col_field1)
        self.assertIn("defaultValue", col_field1)
        self.assertIsNotNone(col_field1["defaultValue"])
        self.assertIsInstance(col_field1["defaultValue"], str)

        self.assertIn("prefill", col_field2)
        self.assertIn("defaultValue", col_field2)
        self.assertIsNotNone(col_field2["defaultValue"])
        self.assertIsInstance(col_field2["defaultValue"], str)

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

    def test_logging_for_empty_prefill(self):
        config = deepcopy(CONFIGURATION)
        form_step = FormStepFactory.create(form_definition__configuration=config)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()

        @register("demo")
        class EmptyPrefillPlug(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                return {}

        apply_prefill(
            configuration=config,
            submission=submission,
            register=register,
        )

        log = TimelineLogProxy.objects.get()

        self.assertEqual(log.event, "prefill_retrieve_empty")
        expected_message = _(
            "%(lead)s: Prefill plugin %(plugin)s returned empty values"
        ) % {
            "lead": escape_filter(log.fmt_lead),
            "plugin": escape_filter(log.fmt_plugin),
        }
        self.assertEqual(log.get_message().strip(), expected_message)

    def test_prefill_exception(self):
        configuration = deepcopy(CONFIGURATION)
        form_step = FormStepFactory.create(form_definition__configuration=configuration)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()

        @register("demo")
        class ErrorPrefill(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                raise Exception("boo")

        with self.assertLogs(level=logging.ERROR):
            new_configuration = apply_prefill(
                configuration=configuration,
                submission=submission,
                register=register,
            )

        field = new_configuration["components"][0]
        self.assertIsNone(field["defaultValue"])

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

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_applying_prefill_plugins_not_enabled(self, mock_get_solo):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"prefill": {"demo": {"enabled": False}}}
        )

        with self.assertRaises(PluginNotEnabled):
            apply_prefill(
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
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)
        self.assertEqual("", field["defaultValue"])

    def test_value_is_normalized(self):
        """
        Regression integration test for #1693.

        Ensure that values retrieved from prefill plugins are normalized according
        to the postal code inputMask.
        """
        configuration = {
            "components": [
                {
                    "type": "postcode",
                    "key": "postcode",
                    "inputMask": "9999 AA",
                    "prefill": {
                        "plugin": "postcode",
                        "attribute": "static",
                    },
                    "defaultValue": "",
                }
            ]
        }

        form_step = FormStepFactory.create(form_definition__configuration=configuration)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()

        @register("postcode")
        class HavePlugin(DemoPrefill):
            @staticmethod
            def get_prefill_values(submission, attributes):
                return {"static": "1015CJ"}

        new_configuration = apply_prefill(
            configuration=configuration, submission=submission, register=register
        )

        field = new_configuration["components"][0]
        self.assertEqual(field["defaultValue"], "1015 CJ")

    @patch("openforms.prefill.tests.test_prefill_hook.DemoPrefill.get_prefill_values")
    def test_prefill_form_with_multiple_steps(self, m_get_prefill_value):
        m_get_prefill_value.return_value = {"random_isodate": "2020-12-12"}

        configuration1 = {
            "display": "form",
            "components": [
                {
                    "key": "textFieldA",
                    "type": "textfield",
                }
            ],
        }
        configuration2 = {
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
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form_definition__configuration=configuration1, form=form
        )
        FormStepFactory.create(form_definition__configuration=configuration2, form=form)
        submission = SubmissionFactory.create(form=form)

        # Doesn't raise KeyError
        apply_prefill(
            configuration=form_step1.form_definition.configuration,
            submission=submission,
            register=register,
        )
