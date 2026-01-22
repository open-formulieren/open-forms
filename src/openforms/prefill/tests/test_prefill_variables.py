from datetime import date
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase, tag

import requests_mock
from rest_framework import serializers
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.formio.service import (
    FormioConfigurationWrapper,
    get_dynamic_configuration,
)
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ..contrib.demo.plugin import DemoPrefill
from ..exceptions import PrefillSkipped
from ..service import prefill_variables
from .utils import get_test_register

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


class PrefillVariablesTests(TestCase):
    @patch(
        "openforms.prefill.service.fetch_prefill_values_from_attribute",
        return_value={"voornamen": "Not so random string", "age": 123},
    )
    def test_applying_prefill_plugin_from_component_conf(self, m_prefill):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form, form_step=form_step
        )

        prefill_variables(submission=submission_step.submission)

        submission_value_variables_state = (
            submission_step.submission.load_submission_value_variables_state()
        )

        self.assertEqual(2, len(submission_value_variables_state.variables))

        submission_variable1 = submission_value_variables_state.get_variable(
            key="voornamen"
        )
        submission_variable2 = submission_value_variables_state.get_variable(key="age")

        self.assertEqual("Not so random string", submission_variable1.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable1.source
        )
        self.assertEqual(123, submission_variable2.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable2.source
        )

    @patch(
        "openforms.prefill.service.fetch_prefill_values_from_attribute",
        return_value={"voornamen": "Not so random string"},
    )
    def test_applying_prefill_plugin_from_user_defined_with_attribute(self, m_prefill):
        submission = SubmissionFactory.create()
        FormVariableFactory.create(
            key="voornamen",
            form=submission.form,
            prefill_plugin="demo",
            prefill_attribute="random_string",
        )

        prefill_variables(submission=submission)

        submission_value_variables_state = (
            submission.load_submission_value_variables_state()
        )

        self.assertEqual(1, len(submission_value_variables_state.variables))

        submission_variable = submission_value_variables_state.get_variable(
            key="voornamen"
        )

        self.assertEqual("Not so random string", submission_variable.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable.source
        )

    @patch(
        "openforms.prefill.service.fetch_prefill_values_from_attribute",
        return_value={
            "postcode": "1015CJ",
            "birthDate": "19990615",
            "user_defined": "20000101",
        },
    )
    def test_normalization_applied(self, m_prefill):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
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
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "birthDate",
                        "prefill": {
                            "plugin": "birthDate",
                            "attribute": "static",
                        },
                        "defaultValue": "",
                    }
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            name="user_defined",
            key="user_defined",
            data_type=FormVariableDataTypes.date,
            user_defined=True,
            prefill_plugin="birthDate",
            prefill_attribute="static",
        )
        submission = SubmissionFactory.create(form=form)
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
        )

        prefill_variables(submission=submission)

        assert submission_step1.form_step is not None
        config_wrapper1 = FormioConfigurationWrapper(
            submission_step1.form_step.form_definition.configuration
        )
        dynamic_config1 = get_dynamic_configuration(
            config_wrapper1,
            submission=submission,
        )
        assert submission_step2.form_step is not None
        config_wrapper2 = FormioConfigurationWrapper(
            submission_step2.form_step.form_definition.configuration
        )
        dynamic_config2 = get_dynamic_configuration(
            config_wrapper2,
            submission=submission,
        )

        component_postcode = dynamic_config1.configuration["components"][0]
        self.assertEqual(component_postcode["type"], "postcode")
        assert "defaultValue" in component_postcode
        self.assertEqual(component_postcode["defaultValue"], "1015 CJ")

        component_date = dynamic_config2.configuration["components"][0]
        self.assertEqual(component_date["type"], "date")
        assert "defaultValue" in component_date
        self.assertEqual(component_date["defaultValue"], "1999-06-15")

        state = submission.load_submission_value_variables_state()
        self.assertEqual(
            state.get_prefilled_data().data,
            {
                "birthDate": date(1999, 6, 15),
                "postcode": "1015 CJ",
                "user_defined": date(2000, 1, 1),
            },
        )

    def test_prefill_variables_are_retrieved_when_form_variables_deleted(self):
        form_step = FormStepFactory.create(form_definition__configuration=CONFIGURATION)
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
            data={"voornamen": "", "age": None},
        )

        submission_value_variables_state = (
            submission_step.submission.load_submission_value_variables_state()
        )

        FormVariable.objects.all().delete()

        prefill_variables = submission_value_variables_state.prefilled_variables
        self.assertEqual(2, len(prefill_variables))


prefill_from_options_register = get_test_register()


class OptionsSerializer(serializers.Serializer):
    var_key = serializers.CharField(required=True)
    var_value = serializers.CharField(required=True)
    crash_ownership_check = serializers.BooleanField(default=False, required=False)


@prefill_from_options_register("ownership-check-passes")
class OwnershipCheckPassesPlugin(DemoPrefill):
    options = OptionsSerializer

    def verify_initial_data_ownership(
        self, submission: Submission, prefill_options
    ) -> None:
        assert prefill_options
        if prefill_options["crash_ownership_check"]:
            raise Exception("crash and burn")

    @classmethod
    def get_prefill_values_from_options(
        cls, submission: Submission, options, submission_value_variable
    ):
        return {options["var_key"]: options["var_value"]}


@prefill_from_options_register("ownership-check-fails")
class OwnershipCheckFailsPlugin(DemoPrefill):
    options = OptionsSerializer

    def verify_initial_data_ownership(
        self, submission: Submission, prefill_options
    ) -> None:
        raise PermissionDenied("you shall not pass")

    @classmethod
    def get_prefill_values_from_options(
        cls, submission: Submission, options, submission_value_variable
    ):
        return {options["var_key"]: options["var_value"]}


@prefill_from_options_register("prefill-skipped")
class PrefillSkippedPlugin(DemoPrefill):
    options = OptionsSerializer

    @classmethod
    def get_prefill_values_from_options(
        cls, submission: Submission, options, submission_value_variable
    ):
        raise PrefillSkipped("Prefill was skipped")


@prefill_from_options_register("generic-exception")
class GenericExceptionPlugin(DemoPrefill):
    options = OptionsSerializer

    @classmethod
    def get_prefill_values_from_options(
        cls, submission: Submission, options, submission_value_variable
    ):
        raise Exception("Generic exception")


class PrefillVariablesFromOptionsTests(TestCase):
    @patch(
        "openforms.prefill.service.fetch_prefill_values_from_options",
        return_value={
            "object_data": {
                "voornamen": "Not so random string",
            },
            "voornamen": "Not so random string",
        },
    )
    def test_applying_prefill_plugin_from_user_defined_with_options(self, m_prefill):
        submission = SubmissionFactory.create()
        FormVariableFactory.create(
            key="voornamen", form=submission.form, user_defined=True
        )
        FormVariableFactory.create(
            key="object_data",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": "objects-group",
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
        )

        prefill_variables(submission=submission)

        variables_state = submission.load_submission_value_variables_state(refresh=True)
        self.assertEqual(len(variables_state.variables), 2)
        submission_variable = variables_state.get_variable(key="voornamen")
        self.assertEqual("Not so random string", submission_variable.value)
        self.assertEqual(
            SubmissionValueVariableSources.prefill, submission_variable.source
        )

    def test_applying_prefill_plugin_from_user_defined_with_invalid_options(self):
        submission = SubmissionFactory.create()
        FormVariableFactory.create(
            key="voornamen",
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": "Wrong value",
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
        )

        prefill_variables(submission=submission)

        self.assertEqual(TimelineLogProxy.objects.count(), 1)
        logs = TimelineLogProxy.objects.get()

        self.assertEqual(logs.extra_data["log_event"], "prefill_retrieve_failure")
        self.assertIn("objects_api_group", logs.extra_data["error"])

    @tag("gh-4398")
    def test_verify_initial_data_ownership_only_called_with_initial_data_reference(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=form, key="voornamen", user_defined=True)
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="ownership-check-fails",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
            },
        )

        with self.subTest("called with initial data reference"):
            submission1 = SubmissionFactory.create(
                form=form,
                auth_info__value="111222333",
                auth_info__attribute=AuthAttribute.bsn,
                initial_data_reference="some reference",
            )

            with self.assertRaises(PermissionDenied):
                prefill_variables(
                    submission=submission1, register=prefill_from_options_register
                )

            logs = TimelineLogProxy.objects.for_object(submission1)
            self.assertEqual(logs.filter_event("prefill_retrieve_failure").count(), 1)
            self.assertFalse(
                logs.filter_event("object_ownership_check_success").exists()
            )
            self.assertFalse(logs.filter_event("prefill_retrieve_success").exists())

        with self.subTest("called without initial data reference"):
            submission2 = SubmissionFactory.create(
                form=form,
                auth_info__value="111222333",
                auth_info__attribute=AuthAttribute.bsn,
                initial_data_reference="",
            )
            try:
                prefill_variables(
                    submission=submission2, register=prefill_from_options_register
                )
            except PermissionDenied as exc:
                raise self.failureException("Ownerhip check not expected") from exc

            logs = TimelineLogProxy.objects.for_object(submission2)
            self.assertEqual(logs.filter_event("prefill_retrieve_success").count(), 1)
            self.assertFalse(logs.filter_event("prefill_retrieve_failure").exists())
            self.assertFalse(
                logs.filter_event("object_ownership_check_success").exists()
            )

    @tag("gh-4398")
    def test_verify_initial_data_ownership_error_fails_prefill_entirely(self):
        # These situations need to be visible in Sentry/error monitoring as they're
        # unexpected crashes (and likely programming mistakes)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="ownership-check-passes",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
                "crash_ownership_check": True,
            },
        )

        submission = SubmissionFactory.create(
            form=form,
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference="some reference",
        )

        with self.assertRaisesMessage(Exception, "crash and burn"):
            prefill_variables(
                submission=submission, register=prefill_from_options_register
            )

        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertFalse(logs.filter_event("prefill_retrieve_failure").exists())
        self.assertFalse(logs.filter_event("prefill_retrieve_success").exists())

    def test_successfull_verification_runs_prefill(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=form, key="voornamen", user_defined=True)
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="ownership-check-passes",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
                "crash_ownership_check": False,
            },
        )
        submission = SubmissionFactory.create(
            form=form,
            auth_info__value="111222333",
            auth_info__attribute=AuthAttribute.bsn,
            initial_data_reference="some reference",
        )

        prefill_variables(submission=submission, register=prefill_from_options_register)

        variables_state = submission.load_submission_value_variables_state()
        self.assertEqual(variables_state.get_data()["voornamen"], "foo, bar")

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    def test_plugin_not_enabled(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"prefill": {"demo": {"enabled": False}}}
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=form, key="voornamen", user_defined=True)
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="demo",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
            },
        )
        submission = SubmissionFactory.create(form=form)

        prefill_variables(submission=submission, register=prefill_from_options_register)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(variables_state.get_data(), {})

    def test_prefill_skipped_exception(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=form, key="voornamen", user_defined=True)
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="prefill-skipped",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
            },
        )
        submission = SubmissionFactory.create(form=form)

        prefill_variables(submission=submission, register=prefill_from_options_register)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(variables_state.get_data(), {})

    def test_prefill_generic_exception(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                    }
                ],
            },
        )
        FormVariableFactory.create(form=form, key="voornamen", user_defined=True)
        FormVariableFactory.create(
            form=form,
            key="prefillData",
            user_defined=True,
            prefill_plugin="generic-exception",
            prefill_options={
                "var_key": "voornamen",
                "var_value": "foo, bar",
            },
        )
        submission = SubmissionFactory.create(form=form)

        prefill_variables(submission=submission, register=prefill_from_options_register)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(variables_state.get_data(), {})


class PrefillVariablesTransactionTests(TransactionTestCase):
    @requests_mock.Mocker()
    @patch("openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo")
    def test_no_success_message_on_failure(self, m, m_solo):
        service = ServiceFactory.build(api_root="https://personen/api/")
        m.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=404,
        )
        m_solo.return_value = HaalCentraalConfig(brp_personen_service=service)
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                        "prefill": {
                            "plugin": "haalcentraal",
                            "attribute": "test-field",
                        },
                        "defaultValue": "",
                    }
                ]
            }
        )
        submission_step = SubmissionStepFactory.create(
            submission__form=form_step.form,
            form_step=form_step,
            submission__auth_info__value="999990676",
            submission__auth_info__attribute=AuthAttribute.bsn,
        )

        prefill_variables(submission=submission_step.submission)

        logs = TimelineLogProxy.objects.filter(object_id=submission_step.submission.id)

        for log in logs:
            self.assertNotEqual(log.event, "prefill_retrieve_success")
