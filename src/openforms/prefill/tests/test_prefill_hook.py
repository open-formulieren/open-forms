from collections.abc import Sequence
from copy import deepcopy
from unittest.mock import patch

from django.template.defaultfilters import escape_filter
from django.test import TransactionTestCase
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from openforms.authentication.service import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.typing import Component, FormioConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.logging.models import TimelineLogProxy
from openforms.plugins.exceptions import PluginNotEnabled
from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONEncodable

from ..base import BasePlugin
from ..constants import IdentifierRoles
from ..contrib.demo.plugin import DemoPrefill
from ..exceptions import PrefillSkipped
from ..registry import Registry, register as prefill_register
from ..service import inject_prefill, prefill_variables
from .utils import get_test_register

register = get_test_register()

CONFIGURATION: FormioConfiguration = {
    "display": "form",
    "components": [
        {
            "id": "e4ty7zs",
            "key": "voornamen",
            "type": "textfield",
            "label": "Voornamen",
            "hidden": False,
            "prefill": {
                "plugin": "demo",
                "attribute": "random_string",
                "identifierRole": IdentifierRoles.main,
            },
            "tooltip": "",
            "multiple": False,
            "validate": {
                "pattern": "",
                "required": False,
            },
            "clearOnHide": True,
            "conditional": {"eq": "", "show": None, "when": None},
            "description": "",
            "placeholder": "",
            "showInEmail": False,
            "defaultValue": "",
        }
    ],
}


def apply_prefill(
    configuration: FormioConfiguration, submission: "Submission", register=None
) -> FormioConfiguration:
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
    @patch(
        "openforms.prefill.contrib.haalcentraal_brp.plugin.HaalCentraalPrefill.get_prefill_values",
        return_value={"naam.voornamen": "John", "naam.geslachtsnaam": "Dodo"},
    )
    def test_fetch_values_with_multiple_people(self, m_haal_centraal):
        components: Sequence[Component] = [
            {
                "key": "mainPersonName",
                "type": "textfield",
                "label": "mainPersonName",
                "prefill": {
                    "plugin": "haalcentraal",
                    "attribute": "naam.voornamen",
                    "identifierRole": IdentifierRoles.main,
                },
            },
            {
                "key": "authorisedPersonSurname",
                "type": "textfield",
                "label": "authorisedPersonSurname",
                "prefill": {
                    "plugin": "haalcentraal",
                    "attribute": "naam.geslachtsnaam",
                    "identifierRole": IdentifierRoles.authorizee,
                },
            },
        ]
        submission = SubmissionFactory.from_components(components_list=components)

        apply_prefill(
            configuration={"components": components},
            submission=submission,
            register=prefill_register,
        )

        name_main = SubmissionValueVariable.objects.get(key="mainPersonName")
        surname_authorised_person = SubmissionValueVariable.objects.get(
            key="authorisedPersonSurname"
        )

        self.assertEqual(name_main.value, "John")
        self.assertEqual(surname_authorised_person.value, "Dodo")

    @patch(
        "openforms.prefill.contrib.haalcentraal_brp.plugin.HaalCentraalPrefill.get_prefill_values",
        return_value={"naam.voornamen": "John", "naam.geslachtsnaam": "Dodo"},
    )
    @patch(
        "openforms.prefill.contrib.kvk.plugin.KVK_KVKNumberPrefill.get_prefill_values",
        return_value={"bezoekadres.postcode": "1111 AA"},
    )
    def test_fetch_values_with_legal_entity_and_person(self, m_kvk, m_haal_centraal):
        components: Sequence[Component] = [
            {
                "key": "companyPostcode",
                "type": "postcode",
                "label": "companyPostcode",
                "prefill": {
                    "plugin": "kvk-kvknumber",
                    "attribute": "bezoekadres.postcode",
                    "identifierRole": IdentifierRoles.main,
                },
            },
            {
                "key": "authorisedPersonSurname",
                "type": "textfield",
                "label": "authorisedPersonSurname",
                "prefill": {
                    "plugin": "haalcentraal",
                    "attribute": "naam.geslachtsnaam",
                    "identifierRole": IdentifierRoles.authorizee,
                },
            },
            {
                "key": "authorisedPersonName",
                "type": "textfield",
                "label": "authorisedPersonName",
                "prefill": {
                    "plugin": "haalcentraal",
                    "attribute": "naam.voornamen",
                    "identifierRole": IdentifierRoles.authorizee,
                },
            },
        ]
        submission = SubmissionFactory.from_components(components_list=components)

        apply_prefill(
            configuration={"components": components},
            submission=submission,
            register=prefill_register,
        )

        postcode_main = SubmissionValueVariable.objects.get(key="companyPostcode")
        name_authorised_person = SubmissionValueVariable.objects.get(
            key="authorisedPersonName"
        )
        surname_authorised_person = SubmissionValueVariable.objects.get(
            key="authorisedPersonSurname"
        )

        self.assertEqual(postcode_main.value, "1111 AA")
        self.assertEqual(name_authorised_person.value, "John")
        self.assertEqual(surname_authorised_person.value, "Dodo")

    def test_applying_prefill_plugins(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission = SubmissionFactory.create(form=form_step.form)

        new_configuration = apply_prefill(
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)

        with self.subTest("Log event display (gh-5188)"):
            log_events = TimelineLogProxy.objects.filter_event(
                "prefill_retrieve_success"
            )
            self.assertEqual(len(log_events), 1)
            log = log_events[0]
            self.assertIn("Voornamen (random_string)", log.get_message())

    def test_complex_components(self):
        def config_factory():
            components = deepcopy(CONFIGURATION["components"])
            for comp in components:
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

        field = fieldset["components"][0]  # type: ignore - can't narrow to FieldsetComponent
        self.assertIn("prefill", field)
        self.assertIn("defaultValue", field)
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)

        column1, column2 = new_configuration["components"][1]["columns"]  # type: ignore - can't narrow to ColumnsComponent
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
            def get_prefill_values(*args, **kwargs):
                return {}

        new_configuration = apply_prefill(
            configuration=form_step.form_definition.configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
        self.assertIsNotNone(field["defaultValue"])
        self.assertEqual(field["defaultValue"], "some-default")

    def test_logging_for_empty_prefill(self):
        config = deepcopy(CONFIGURATION)
        form_step = FormStepFactory.create(form_definition__configuration=config)
        submission = SubmissionFactory.create(form=form_step.form)

        register = Registry()

        @register("demo")
        class EmptyPrefillPlug(DemoPrefill):
            @classmethod
            def get_prefill_values(
                cls, submission, attributes, identifier_role=IdentifierRoles.main
            ):
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
            "plugin": escape_filter(str(log.fmt_plugin)),
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
            def get_prefill_values(*args, **kwargs):
                raise Exception("boo")

        new_configuration = apply_prefill(
            configuration=configuration,
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
        self.assertEqual(field["defaultValue"], "")

    def tests_no_prefill_configured(self):
        config = deepcopy(CONFIGURATION)
        config["components"][0]["prefill"] = {
            "plugin": "",
            "attribute": "",
            "identifierRole": IdentifierRoles.main,
        }
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

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
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
                    "defaultValue": "",
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
        assert "defaultValue" in field
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
                    "defaultValue": "",
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
        assert "defaultValue" in field
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
                    "defaultValue": "",
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
        assert "defaultValue" in field
        self.assertIsNotNone(field["defaultValue"])
        self.assertIsInstance(field["defaultValue"], str)
        self.assertEqual("", field["defaultValue"])

    def test_value_is_normalized(self):
        """
        Regression integration test for #1693.

        Ensure that values retrieved from prefill plugins are normalized according
        to the postal code inputMask.
        """
        configuration: FormioConfiguration = {
            "components": [
                {
                    "type": "postcode",
                    "key": "postcode",
                    "label": "postcode",
                    "inputMask": "9999 AA",  # type: ignore - can't narrow to postcode component
                    "prefill": {
                        "plugin": "postcode",
                        "attribute": "static",
                        "identifierRole": IdentifierRoles.main,
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
            @classmethod
            def get_prefill_values(
                cls, submission, attributes, identifier_role=IdentifierRoles.main
            ) -> dict[str, JSONEncodable]:
                return {"static": "1015CJ"}

        new_configuration = apply_prefill(
            configuration=configuration, submission=submission, register=register
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
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
                    "label": "textFieldA",
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
                    "defaultValue": "",
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

    def test_demo_prefill_get_identifier_not_authenticated(self):
        plugin = DemoPrefill(identifier="demo")

        submission = SubmissionFactory.create()
        assert not submission.is_authenticated

        result = plugin.get_identifier_value(submission, IdentifierRoles.main)

        self.assertIsNone(result)

    def test_demo_prefill_get_identifier_authenticated(self):
        class TestPlugin(BasePlugin):
            requires_auth = (AuthAttribute.bsn,)

        plugin = TestPlugin(identifier="test")

        submission = SubmissionFactory.create(
            auth_info__value="123123123", auth_info__attribute=AuthAttribute.bsn
        )
        assert submission.is_authenticated

        result = plugin.get_identifier_value(submission, IdentifierRoles.main)

        self.assertEqual("123123123", result)

    def test_prefill_logging_with_mismatching_login_method(self):
        components: Sequence[Component] = [
            {
                "key": "mainPersonName",
                "type": "textfield",
                "label": "mainPersonName",
                "prefill": {
                    "plugin": "demo",
                    "attribute": "naam.voornamen",
                    "identifierRole": IdentifierRoles.main,
                },
            },
        ]
        submission = SubmissionFactory.from_components(
            components_list=components, kvk="69599084"
        )
        register = Registry()

        @register("demo")
        class MismatchPlugin(DemoPrefill):
            requires_auth = (AuthAttribute.bsn,)

            @classmethod
            def get_prefill_values(
                cls, submission, attributes, identifier_role=IdentifierRoles.main
            ):
                return {}

        apply_prefill(
            configuration={"components": components},
            submission=submission,
            register=register,
        )

        self.assertFalse(TimelineLogProxy.objects.exists())

    def test_prefill_skipped_exception(self):
        components: Sequence[Component] = [
            {
                "key": "mainPersonName",
                "type": "textfield",
                "label": "mainPersonName",
                "prefill": {
                    "plugin": "demo",
                    "attribute": "naam.voornamen",
                    "identifierRole": IdentifierRoles.main,
                },
            },
        ]
        submission = SubmissionFactory.from_components(components_list=components)
        register = Registry()

        @register("demo")
        class PrefillSkippedPlugin(DemoPrefill):
            requires_auth = (AuthAttribute.bsn,)

            @classmethod
            def get_prefill_values(
                cls, submission, attributes, identifier_role=IdentifierRoles.main
            ):
                raise PrefillSkipped("Prefill was skipped")

        new_configuration = apply_prefill(
            configuration={"components": components},
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
        self.assertEqual(field["defaultValue"], "")

    def test_prefill_generic_exception(self):
        components: Sequence[Component] = [
            {
                "key": "mainPersonName",
                "type": "textfield",
                "label": "mainPersonName",
                "prefill": {
                    "plugin": "demo",
                    "attribute": "naam.voornamen",
                    "identifierRole": IdentifierRoles.main,
                },
            },
        ]
        submission = SubmissionFactory.from_components(components_list=components)
        register = Registry()

        @register("demo")
        class PrefillGenericExceptionPlugin(DemoPrefill):
            requires_auth = (AuthAttribute.bsn,)

            @classmethod
            def get_prefill_values(
                cls, submission, attributes, identifier_role=IdentifierRoles.main
            ):
                raise Exception("Generic exception")

        new_configuration = apply_prefill(
            configuration={"components": components},
            submission=submission,
            register=register,
        )

        field = new_configuration["components"][0]
        assert "defaultValue" in field
        self.assertEqual(field["defaultValue"], "")
