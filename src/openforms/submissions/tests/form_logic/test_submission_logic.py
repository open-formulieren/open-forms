import json
from unittest import expectedFailure

from django.db import connection
from django.test import override_settings, tag

from freezegun import freeze_time
from hypothesis.extra.django import TestCase as HypothesisTestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.typing import JSONValue
from openforms.utils.json_logic.api.validators import JsonLogicValidator
from openforms.variables.constants import FormVariableDataTypes

from ..factories import SubmissionFactory, SubmissionStepFactory
from ..mixins import SubmissionsMixin


class CheckLogicSubmissionTest(SubmissionsMixin, APITestCase):
    def test_check_logic_on_whole_submission(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "driverId",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "<": [
                    {"var": "age"},
                    18,
                ]
            },
            actions=[
                {
                    "form_step_uuid": f"{step2.uuid}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"age": 16},
        )

        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-detail",
            kwargs={"uuid": submission.uuid},
        )
        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertFalse(data["steps"][1]["isApplicable"])

    @tag("gh-1913")
    def test_check_logic_on_whole_submission_with_variables(self):
        """
        Assert that the submission logic check takes all variables into account.

        * We only submit step1 and not step2, while setting up a logic rule that only
          becomes relevant from step3 onwards
        * We include calculated variables that determine the availability of step3
        """
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    }
                ]
            },
        )
        # we don't progress through these and set up user-defined variables, so it doesn't matter
        # that there are no components.
        step2 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        step3 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        # set up a number of variables to mutate with logic
        FormVariableFactory.create(
            form=form,
            key="var1",
            user_defined=True,
            data_type=FormVariableDataTypes.float,
        )
        FormVariableFactory.create(
            form=form,
            key="var2",
            user_defined=True,
            data_type=FormVariableDataTypes.float,
            initial_value=0,
        )
        FormVariableFactory.create(
            form=form,
            key="var3",
            user_defined=True,
            data_type=FormVariableDataTypes.float,
        )
        # set up logic rules:
        # 1. set the variable var1 to the value 10, always
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "variable": "var1",
                    "action": {"type": "variable", "value": 10},
                }
            ],
        )
        # 2. set the variable var2 to the value 5, only from step3
        FormLogicFactory.create(
            form=form,
            trigger_from_step=step3,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "variable": "var2",
                    "action": {"type": "variable", "value": 5},
                }
            ],
        )
        # 3. set the variable var3 to the sum of var1 and var2, always.
        # In this test, the resulting value is 10 (10 + 0) because step3 has not been reached.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "variable": "var3",
                    "action": {
                        "type": "variable",
                        "value": {"+": [{"var": "var1"}, {"var": "var2"}]},
                    },
                }
            ],
        )
        # 4. Disable step 2 if var1 is not equal to 10 - this should not happen because
        # we always set it
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!=": [{"var": "var1"}, 10]},
            actions=[
                {
                    "form_step_uuid": str(step2.uuid),
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        # if the rule gets executed that sets var2 to 5, then the total is 15 (which
        # should not happen). We can verify this by blocking submission.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!=": [{"var": "var3"}, 15]},
            actions=[
                {
                    "action": {
                        "type": "disable-next",
                    },
                }
            ],
        )
        # create a submission where only step1 is submitted
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"text1": "trigger-rule"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-detail", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertTrue(data["steps"][1]["isApplicable"])
        self.assertFalse(data["steps"][1]["canSubmit"])

    @tag("gh-4579")
    def test_properly_determine_current_step(self):
        """
        Assert that the submission logic check properly determines the current step for
        rules that define `triggerFromStep`

        * We fill out step 1 and continue to step 2
        * In step two the logic rule triggers that prevents us from continuing
        * We go back to step 1 and it should be possible to continue to step 2 from there
        """
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text2",
                    }
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="verdergaan",
            user_defined=True,
            data_type=FormVariableDataTypes.string,
        )
        # set up logic rules:
        # 1. setting `text1` to `trigger-value` should set our user defined variable to `nee`
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "component": "",
                    "variable": "verdergaan",
                    "formStepUuid": None,
                    "action": {"type": "variable", "value": "nee"},
                }
            ],
        )
        # 2. if `verdergaan` is `nee`, block going to step3
        FormLogicFactory.create(
            form=form,
            trigger_from_step=step2,
            json_logic_trigger={"==": [{"var": "verdergaan"}, "nee"]},
            actions=[
                {
                    "component": "",
                    "formStepUuid": None,
                    "action": {"type": "disable-next"},
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        with self.subTest("fill in step1"):
            endpoint = reverse(
                "api:submission-steps-detail",
                kwargs={
                    "submission_uuid": submission.uuid,
                    "step_uuid": step1.uuid,
                },
            )

            response = self.client.put(
                endpoint, data={"data": {"text1": "trigger-rule"}}
            )

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

            data = response.json()

            self.assertTrue(data["completed"])
            self.assertTrue(data["canSubmit"])

        with self.subTest("logic step for step 2 should not allow submitting"):
            endpoint = reverse(
                "api:submission-steps-logic-check",
                kwargs={"submission_uuid": submission.uuid, "step_uuid": step2.uuid},
            )
            response = self.client.post(endpoint, data={"data": {"text2": "foo"}})

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            data = response.json()

            self.assertFalse(data["step"]["canSubmit"])

        with self.subTest("logic check for step 1 should still allow submitting"):
            endpoint = reverse(
                "api:submission-steps-logic-check",
                kwargs={"submission_uuid": submission.uuid, "step_uuid": step1.uuid},
            )

            response = self.client.post(
                endpoint, data={"data": {"text1": "trigger-rule"}}
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            data = response.json()

            # It should be possible to go to the next step, because the logic rule
            # to block going to the next step should only trigger from step2
            self.assertTrue(data["step"]["canSubmit"])

    def test_check_logic_with_full_datetime(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "driverId",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "<": [
                    {"date": {"var": "dateOfBirth"}},
                    {"date": "2021-01-01"},
                ]
            },
            actions=[
                {
                    "form_step_uuid": f"{step2.uuid}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"dateOfBirth": "2020-01-01T00:00:00+01:00"},
        )

        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-detail",
            kwargs={"uuid": submission.uuid},
        )
        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertFalse(data["steps"][1]["isApplicable"])

    @tag("gh-1755")
    def test_check_logic_hide_with_default_value(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "hidden": True,
                        "clearOnHide": True,
                        "defaultValue": "Test data",
                    },
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "hidden": False,
                    },
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "checkbox"},
                    True,
                ]
            },
            actions=[
                {
                    "component": "textfield",
                    "action": {
                        "name": "Hide element",
                        "type": "property",
                        "property": {
                            "type": "bool",
                            "value": "hidden",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        submission_detail_endpoint = reverse(
            "api:submission-detail",
            kwargs={"uuid": submission.uuid},
        )
        response = self.client.get(submission_detail_endpoint)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )

        response = self.client.post(
            logic_check_endpoint, data={"data": {"checkbox": True}}
        )
        data = response.json()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(
            data["step"]["formStep"]["configuration"]["components"][0]["hidden"],
        )

        response = self.client.post(
            logic_check_endpoint,
            data={"data": {"checkbox": False, "textfield": "Test data"}},
        )
        data = response.json()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"textfield": ""}, data["step"]["data"])
        self.assertTrue(
            data["step"]["formStep"]["configuration"]["components"][0]["hidden"],
        )

    @tag("gh-5151")
    def test_check_logic_hide_map_component(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "textfield",
                    },
                    {
                        "key": "map",
                        "type": "map",
                        "label": "map",
                        "hidden": True,
                        "clearOnHide": True,
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )

        response = self.client.post(logic_check_endpoint, {"data": {"textfield": ""}})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Even though 'map' is missing in the data, the logic check shouldn't return an
        # empty value for it. Ticket #5151
        new_value = response.json()["step"]["data"]
        self.assertEqual(new_value, {})

    def test_response_contains_submission(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "driving",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"-": [{"today": []}, {"rdelta": [18]}]},
                ]
            },
            actions=[
                {
                    "form_step_uuid": f"{form_step2.uuid}",
                    "action": {
                        "name": "Make step not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"dateOfBirth": "2003-01-01"},
        )
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step1.uuid},
        )
        self._add_submission_to_session(submission)

        with freeze_time("2015-10-10"):
            response = self.client.post(endpoint, {"data": submission.data})

        submission_details = response.json()

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(submission_details["submission"]["steps"][1]["isApplicable"])

    def test_with_default_values(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "hide",
                        "defaultValue": True,
                    },
                    {
                        "type": "textfield",
                        "key": "when-unchecked",
                        "hidden": False,
                    },
                    {
                        "type": "textfield",
                        "key": "when-checked",
                        "hidden": False,
                    },
                ]
            },
        )
        # display checked textfield when checkbox is checked, hide the unchecked one
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "hide"}, True]},
            actions=[
                {
                    "formStep": None,
                    "component": "when-unchecked",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                },
                {
                    "formStep": None,
                    "component": "when-checked",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": False,
                    },
                },
            ],
        )
        # hide checked textfield when checkbox is unchecked, display the unchecked one
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "hide"}, False]},
            actions=[
                {
                    "formStep": None,
                    "component": "when-unchecked",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": False,
                    },
                },
                {
                    "formStep": None,
                    "component": "when-checked",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                },
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        url_kwargs = {
            "submission_uuid": submission.uuid,
            "step_uuid": form.formstep_set.get().uuid,
        }
        endpoint = reverse("api:submission-steps-detail", kwargs=url_kwargs)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check", kwargs=url_kwargs
        )

        with self.subTest("Initial call without data"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            configuration = response.json()["formStep"]["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "type": "textfield",
                    "hidden": True,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "type": "textfield",
                    "hidden": False,
                },
            )

        with self.subTest("On explicit un-check"):
            response = self.client.post(logic_check_endpoint, {"data": {"hide": False}})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            configuration = response.json()["step"]["formStep"]["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "type": "textfield",
                    "hidden": False,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "type": "textfield",
                    "hidden": True,
                },
            )

        with self.subTest("On explicit check"):
            response = self.client.post(logic_check_endpoint, {"data": {"hide": True}})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            configuration = response.json()["step"]["formStep"]["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "type": "textfield",
                    "hidden": True,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "type": "textfield",
                    "hidden": False,
                },
            )

    @tag("gh-2054")
    def test_hidden_components_dont_get_cleared_if_they_are_already_empty(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "yes", "value": "yes"},
                            {"label": "no", "value": "no"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "testHidden",
                        "hidden": True,
                        "clearOnHide": True,
                        "defaultValue": "",
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)

        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )
        response = self.client.post(logic_check_endpoint, {"data": {"radio": ""}})

        data = response.json()

        self.assertEqual({}, data["step"]["data"])

    @tag("gh-2340")
    def test_component_values_in_hidden_fieldset_are_cleared(self):
        """
        Components that are children in hidden fieldsets must be cleared when clearOnHide is set.
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "show", "value": "show"},
                            {"label": "hide", "value": "hide"},
                        ],
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "hidden": True,
                        "components": [
                            {
                                "key": "textfield1",
                                "type": "textfield",
                                "clearOnHide": True,
                            },
                            {
                                "key": "textfield2",
                                "type": "textfield",
                                "clearOnHide": False,
                            },
                        ],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "show"]},
            actions=[
                {
                    "component": "fieldset",
                    "action": {
                        "type": "property",
                        "property": {
                            "value": "hidden",
                            "type": "bool",
                        },
                        "state": False,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )

        with self.subTest("values not cleared when fieldset is visible"):
            response = self.client.post(
                logic_check_endpoint,
                {
                    "data": {
                        "radio": "show",
                        "textfield1": "foo",
                        "textfield2": "bar",
                    }
                },
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["step"]["data"], {})

        with self.subTest("one value cleared when fieldset is hidden"):
            response = self.client.post(
                logic_check_endpoint,
                {
                    "data": {
                        "radio": "hide",
                        "textfield1": "foo",
                        "textfield2": "bar",
                    }
                },
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertEqual(data["step"]["data"], {"textfield1": ""})

    @tag("gh-2409")
    @expectedFailure
    def test_component_values_hidden_fieldset_used_in_subsequent_logic(self):
        """
        Test that values that should be cleared can be used safely in other logic rules.

        This is expected to fail until #2409 has been implemented which re-organizes
        the logic evaluation.
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "show", "value": "show"},
                            {"label": "hide", "value": "hide"},
                        ],
                    },
                    {
                        "key": "fieldset",
                        "type": "fieldset",
                        "hidden": True,
                        "components": [
                            {
                                "key": "textfield",
                                "type": "textfield",
                                "clearOnHide": True,
                            },
                        ],
                    },
                    {
                        "key": "calculatedResult",
                        "type": "fieldset",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "show"]},
            actions=[
                {
                    "component": "fieldSet",
                    "action": {
                        "type": "property",
                        "property": {
                            "value": "hidden",
                            "type": "bool",
                        },
                        "state": False,
                    },
                }
            ],
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "textfield"}, "foo"]},
            actions=[
                {
                    "variable": "calculatedResult",
                    "action": {
                        "type": "variable",
                        "value": "bar",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )

        response = self.client.post(
            logic_check_endpoint,
            {
                "data": {
                    "radio": "hide",
                    "textfield": "foo",
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["step"]["data"], {})

    @tag("gh-2827")
    def test_component_value_set_to_now(self):
        """
        Assert that the 'now' variable can be assigned to a component.
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "datetime",
                        "type": "datetime",
                        "label": "Now",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "datetime",
                    "action": {
                        "type": "variable",
                        "value": {"var": "now"},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )

        with freeze_time("2024-03-18T08:31:08+01:00"):
            response = self.client.post(
                logic_check_endpoint, {"data": {"datetime": ""}}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_value = response.json()["step"]["data"]["datetime"]
        # check that the seconds/ms are truncated to prevent infinite logic bouncing.
        # Note that this doesn't make the problem go away 100% - you will get an
        # additional check if the minute value changes, but that should settle after one
        # extra logic check.
        self.assertEqual(new_value, "2024-03-18T07:31:00+00:00")

    def test_component_value_set_to_today(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "date",
                        "type": "date",
                        "label": "Today",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "date",
                    "action": {
                        "type": "variable",
                        "value": {"var": "today"},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )

        with freeze_time("2024-03-18T08:31:08+01:00"):
            response = self.client.post(logic_check_endpoint, {"data": {"date": ""}})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_value = response.json()["step"]["data"]["date"]
        self.assertEqual(new_value, "2024-03-18")

    def test_date_field_not_present_in_step_data_when_assigned_same_value(self):
        """
        Assert that the 'date' field is not present in the step data when a logic action
        sets it to the same value. This shows that we can't rely on the mutations
        returned by `iter_evaluate_rules`, and we need to build up this data diff
        manually after all form logic is evaluated, comparing initial data to final
        data.
        """
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "date",
                    },
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "date",
                    "action": {
                        "type": "variable",
                        "value": "2025-01-01",
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)

        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )
        response = self.client.post(
            logic_check_endpoint, {"data": {"date": "2025-01-01"}}
        )

        data = response.json()

        # The date hasn't changed, so it should not be present in the step data
        self.assertNotIn("date", data["step"]["data"])


def is_valid_expression(expr: dict):
    try:
        JsonLogicValidator()(expr)
    except Exception:
        return False
    return True


def is_jsonb_invariant(value: JSONValue) -> bool:
    serialized = json.dumps(value)
    query = "SELECT %s::jsonb"
    with connection.cursor() as cursor:
        cursor.execute(query, params=(serialized,))
        result = cursor.fetchone()[0]
    return json.loads(result) == value


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class EvaluateLogicSubmissionTest(SubmissionsMixin, APITestCase, HypothesisTestCase):
    def test_evaluate_logic_with_default_values(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "defaultValue": "some-default",
                    },
                    {
                        "type": "textfield",
                        "key": "optional",
                        "hidden": False,
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "name"}, "some-default"]},
            actions=[
                {
                    "formStep": None,
                    "component": "optional",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        configuration = response.json()["formStep"]["configuration"]
        self.assertEqual(
            configuration["components"][1],
            {
                "key": "optional",
                "type": "textfield",
                "hidden": True,
            },
        )

    def test_json_logic_in_trigger_doesnt_raise_error(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "number1",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            key="number2",
            data_type=FormVariableDataTypes.float,
            user_defined=True,
            form=form,
            initial_value="",
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"<": [{"var": "number1"}, {"var": "number2"}]},
            actions=[
                {
                    "action": {
                        "type": "disable-next",
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form.formstep_set.first(),
            data={"number1": "", "number2": 50},
        )
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_json_logic_in_action_doesnt_raise_error(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "number1",
                    },
                    {
                        "type": "number",
                        "key": "number2",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            key="isGreater",
            data_type=FormVariableDataTypes.boolean,
            user_defined=True,
            form=form,
            initial_value=False,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "isGreater",
                    "action": {
                        "type": "variable",
                        "value": {"<": [{"var": "number1"}, {"var": "number2"}]},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form.formstep_set.first(),
            data={"number1": "", "number2": 50},
        )
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
