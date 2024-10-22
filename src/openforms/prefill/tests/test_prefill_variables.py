from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, TransactionTestCase

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
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
from openforms.prefill.contrib.demo.constants import Attributes
from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..service import prefill_variables

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
        "openforms.prefill.service.fetch_prefill_values_from_options",
        return_value={"voornamen": "Not so random string"},
    )
    def test_applying_prefill_plugin_from_user_defined_with_options(self, m_prefill):
        submission = SubmissionFactory.create()
        FormVariableFactory.create(
            key="voornamen",
            form=submission.form,
            prefill_plugin="objects_api",
            prefill_options={
                "objects_api_group": 1,
                "objecttype_uuid": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "variables_mapping": [
                    {"variable_key": "voornamen", "target_path": ["some", "path"]},
                ],
            },
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

    @patch(
        "openforms.prefill.service.fetch_prefill_values_from_attribute",
        return_value={"postcode": "1015CJ", "birthDate": "19990615"},
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

        request = RequestFactory().get("/foo")
        config_wrapper1 = FormioConfigurationWrapper(
            submission_step1.form_step.form_definition.configuration
        )
        dynamic_config1 = get_dynamic_configuration(
            config_wrapper1,
            request=request,
            submission=submission,
        )
        config_wrapper2 = FormioConfigurationWrapper(
            submission_step2.form_step.form_definition.configuration
        )
        dynamic_config2 = get_dynamic_configuration(
            config_wrapper2,
            request=request,
            submission=submission,
        )

        component_postcode = dynamic_config1.configuration["components"][0]
        self.assertEqual(component_postcode["type"], "postcode")
        self.assertEqual(component_postcode["defaultValue"], "1015 CJ")

        component_date = dynamic_config2.configuration["components"][0]
        self.assertEqual(component_date["type"], "date")
        self.assertEqual(component_date["defaultValue"], "1999-06-15")

        variable_postcode = submission.submissionvaluevariable_set.get(key="postcode")
        variable_date = submission.submissionvaluevariable_set.get(key="birthDate")

        self.assertEqual(variable_postcode.value, "1015 CJ")
        self.assertEqual(variable_date.value, "1999-06-15")

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

        prefill_variables = submission_value_variables_state.get_prefill_variables()
        self.assertEqual(2, len(prefill_variables))


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

    def test_verify_initial_data_ownership(self):
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "type": "postcode",
                        "key": "postcode",
                        "inputMask": "9999 AA",
                        "prefill": {
                            "plugin": "demo",
                            "attribute": Attributes.random_string,
                        },
                        "defaultValue": "",
                    }
                ]
            }
        )

        with self.subTest(
            "verify_initial_data_ownership is not called if initial_data_reference is not specified"
        ):
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
                submission__auth_info__value="999990676",
                submission__auth_info__attribute=AuthAttribute.bsn,
            )

            with patch(
                "openforms.prefill.contrib.demo.plugin.DemoPrefill.verify_initial_data_ownership"
            ) as mock_verify_ownership:
                prefill_variables(submission=submission_step.submission)

                mock_verify_ownership.assert_not_called()

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 1
            )

        with self.subTest(
            "verify_initial_data_ownership is called if initial_data_reference is specified"
        ):
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
                submission__auth_info__value="999990676",
                submission__auth_info__attribute=AuthAttribute.bsn,
                submission__initial_data_reference="1234",
            )

            with patch(
                "openforms.prefill.contrib.demo.plugin.DemoPrefill.verify_initial_data_ownership"
            ) as mock_verify_ownership:
                prefill_variables(submission=submission_step.submission)

                mock_verify_ownership.assert_called_once_with(
                    submission_step.submission
                )

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 1
            )

        with self.subTest(
            "verify_initial_data_ownership raising error causes prefill to fail"
        ):
            submission_step = SubmissionStepFactory.create(
                submission__form=form_step.form,
                form_step=form_step,
                submission__auth_info__value="999990676",
                submission__auth_info__attribute=AuthAttribute.bsn,
                submission__initial_data_reference="1234",
            )

            with patch(
                "openforms.prefill.contrib.demo.plugin.DemoPrefill.verify_initial_data_ownership",
                side_effect=PermissionDenied,
            ) as mock_verify_ownership:
                with self.assertRaises(PermissionDenied):
                    prefill_variables(submission=submission_step.submission)

                mock_verify_ownership.assert_called_once_with(
                    submission_step.submission
                )

            logs = TimelineLogProxy.objects.filter(
                object_id=submission_step.submission.id
            )
            self.assertEqual(
                logs.filter(extra_data__log_event="prefill_retrieve_success").count(), 0
            )
