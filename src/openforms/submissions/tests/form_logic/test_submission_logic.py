import json
import textwrap

from django.db import connection
from django.test import override_settings, tag

from freezegun import freeze_time
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
                        "label": "age",
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
                        "label": "driverId",
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
        form.apply_logic_analysis()
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
                        "label": "text1",
                    }
                ]
            },
        )
        # we don't progress through these and set up user-defined variables, so it
        # doesn't matter that there are no components.
        step2 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "number",
                        "label": "Number",
                        "defaultValue": 0,
                    }
                ]
            },
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
            key="var3",
            user_defined=True,
            data_type=FormVariableDataTypes.float,
        )
        # set up logic rules:
        # 1. set the variable var1 to the value 10, step 1
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
        # 2. set number to the value 5, step 3
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "variable": "number",
                    "action": {"type": "variable", "value": 5},
                }
            ],
        )
        # 3. set the variable var3 to the sum of var1 and number, step 1 and 3.
        # In this test, the resulting value is 10 (10 + 0) because step3 has not been reached.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "text1"}, "trigger-rule"]},
            actions=[
                {
                    "variable": "var3",
                    "action": {
                        "type": "variable",
                        "value": {"+": [{"var": "var1"}, {"var": "number"}]},
                    },
                }
            ],
        )
        # 4. Disable step 2 if var1 is not equal to 10 - this should not happen because
        # var1 is set in the first logic rule, so it must have been executed already.
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
        # 5. if the rule gets executed that sets number to 5, then the total is 15
        # (which should not happen). We can verify this by blocking submission.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!=": [{"var": "var3"}, 15]},
            actions=[
                {
                    "form_step_uuid": str(step2.uuid),
                    "action": {
                        "type": "disable-next",
                    },
                }
            ],
        )
        form.apply_logic_analysis()
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
        Assert that the submission logic check properly determines the current step.

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
                        "label": "text1",
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
                        "label": "text2",
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
                    "variable": "verdergaan",
                    "action": {"type": "variable", "value": "nee"},
                }
            ],
        )
        # 2. if `verdergaan` is `nee`, block going to step3
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "verdergaan"}, "nee"]},
            actions=[
                {
                    "form_step_uuid": str(step2.uuid),
                    "action": {"type": "disable-next"},
                }
            ],
        )
        form.apply_logic_analysis()
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
            # to block going to the next step should only trigger on step2
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
                        "label": "dateOfBirth",
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
                        "label": "driverId",
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
        form.apply_logic_analysis()
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
                        "label": "dateOfBirth",
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
                        "label": "driving",
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
        form.apply_logic_analysis()
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

        state = submission.variables_state
        with freeze_time("2015-10-10"):
            response = self.client.post(endpoint, {"data": state.get_data()})

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
                        "label": "hide",
                        "defaultValue": True,
                    },
                    {
                        "type": "textfield",
                        "key": "when-unchecked",
                        "label": "when-unchecked",
                        "hidden": False,
                    },
                    {
                        "type": "textfield",
                        "key": "when-checked",
                        "label": "when-checked",
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
        form.apply_logic_analysis()
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
            configuration = response.json()["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "label": "when-unchecked",
                    "type": "textfield",
                    "hidden": True,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "label": "when-checked",
                    "type": "textfield",
                    "hidden": False,
                },
            )

        with self.subTest("On explicit un-check"):
            response = self.client.post(logic_check_endpoint, {"data": {"hide": False}})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            configuration = response.json()["step"]["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "label": "when-unchecked",
                    "type": "textfield",
                    "hidden": False,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "label": "when-checked",
                    "type": "textfield",
                    "hidden": True,
                },
            )

        with self.subTest("On explicit check"):
            response = self.client.post(logic_check_endpoint, {"data": {"hide": True}})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            configuration = response.json()["step"]["configuration"]
            self.assertEqual(
                configuration["components"][1],
                {
                    "key": "when-unchecked",
                    "label": "when-unchecked",
                    "type": "textfield",
                    "hidden": True,
                },
            )
            self.assertEqual(
                configuration["components"][2],
                {
                    "key": "when-checked",
                    "label": "when-checked",
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
                        "label": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "yes", "value": "yes"},
                            {"label": "no", "value": "no"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "testHidden",
                        "label": "testHidden",
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
                        "label": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "show", "value": "show"},
                            {"label": "hide", "value": "hide"},
                        ],
                    },
                    {
                        "key": "fieldset",
                        "label": "fieldset",
                        "type": "fieldset",
                        "hidden": True,
                        "components": [
                            {
                                "key": "textfield1",
                                "label": "textfield1",
                                "type": "textfield",
                                "clearOnHide": True,
                            },
                            {
                                "key": "textfield2",
                                "label": "textfield2",
                                "type": "textfield",
                                "clearOnHide": False,
                            },
                        ],
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
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
        # Expected to trigger: the hidden textfield should not be in the context during
        # logic evaluation.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield1", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "form_step_uuid": str(form_step.uuid),
                    "action": {"type": "disable-next"},
                }
            ],
        )
        form.apply_logic_analysis()
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
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
            self.assertEqual(data["step"]["data"], {})
            self.assertFalse(data["step"]["canSubmit"])

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
        form.apply_logic_analysis()
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
        form.apply_logic_analysis()
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
                        "label": "date",
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
        form.apply_logic_analysis()
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

    @tag("gh-6001", "gh-6005")
    def test_initial_hidden_visible_through_backend_logic_does_not_nuke_input_data(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "fieldset",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "textfieldClientSide",
                                "label": "textfieldClientSide",
                                "hidden": True,
                                "conditional": {
                                    "show": True,
                                    "when": "checkbox",
                                    "eq": True,
                                },
                            },
                            {
                                "type": "textfield",
                                "key": "textfieldServerSide",
                                "label": "textfieldServerSide",
                                "hidden": True,
                            },
                        ],
                    },
                    {
                        "type": "content",
                        "key": "content",
                        "html": textwrap.dedent(r"""
                        textfieldClientSide: {{ textfieldClientSide }}
                        textfieldServerSide: {{ textfieldServerSide }}
                        """),
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "checkbox"},
            actions=[
                {
                    "formStep": None,
                    "component": "textfieldServerSide",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "value": {},
                        "state": False,
                    },
                }
            ],
        )
        form.apply_logic_analysis()
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        # this simulates:
        # 1. User checkx checkbox, client side logic instantly makes textfieldClientSide
        #    visible
        # 2. Server logic check makes textfieldServerSide visible
        # 3. Input values in both fields, as they're both visible.
        # 4. Value changes trigger new call and we expect to see the values in the
        #    content component HTML.
        response = self.client.post(
            logic_check_endpoint,
            {
                "data": {
                    "checkbox": True,
                    "textfieldClientSide": "client-side-visible",
                    "textfieldServerSide": "server-side-visible",
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        with self.subTest("data mutations"):
            self.assertEqual(data["step"]["data"], {})

        with self.subTest("evaluated content template"):
            content_component = data["step"]["configuration"]["components"][2]
            self.assertEqual(
                content_component["html"],
                textwrap.dedent("""
                textfieldClientSide: client-side-visible
                textfieldServerSide: server-side-visible
                """),
            )

    @tag("gh-6045")
    def test_clear_on_hide_clears_children_of_editgrids(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "outerTextfield",
                        "label": "Outer textfield",
                        "clearOnHide": True,
                    },
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Edit grid",
                        "groupLabel": "item",
                        "clearOnHide": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "innerTextfield",
                                "label": "Inner textfield",
                                "clearOnHide": True,
                            },
                        ],
                    },
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "Checkbox",
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "component": "outerTextfield",
                    "action": {
                        "name": "Hide textfield",
                        "type": "property",
                        "property": {
                            "type": "object",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                },
                {
                    "component": "editgrid",
                    "action": {
                        "name": "Hide edit grid",
                        "type": "property",
                        "property": {
                            "type": "object",
                            "value": "hidden",
                        },
                        "state": True,
                    },
                },
            ],
        )
        form.apply_logic_analysis()
        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        self._add_submission_to_session(submission)

        with self.subTest("initial call after checking checkbox"):
            response_1 = self.client.post(
                endpoint,
                data={
                    "data": {
                        "checkbox": True,
                        "outerTextfield": "clear-me",
                        "editgrid": [{"innerTextfield": "clear-me"}],
                    }
                },
            )

            self.assertEqual(response_1.status_code, status.HTTP_200_OK)
            step_data = response_1.json()["step"]
            # the backend replies with the values as the result of clear-on-hide, where
            # the keys are removed completely. The important part is the updated
            # component configurations, which the renderer handles by itself and *that*
            # leads to the second call.
            self.assertEqual(step_data["data"], {"editgrid": [{}]})

            textfield, editgrid = step_data["configuration"]["components"][0:2]
            self.assertTrue(textfield["hidden"])
            self.assertTrue(editgrid["hidden"])

        # the renderer applies `undefined` to the hidden components, which *removes the
        # keys* from the submission data as well.
        with self.subTest("follow up call after renderer mutations"):
            response_2 = self.client.post(
                endpoint,
                data={
                    "data": {
                        "checkbox": True,
                        # "outerTextfield" key is absent
                        "editgrid": [{}],  # "innerTextfield" key is absent
                    }
                },
            )

            self.assertEqual(response_2.status_code, status.HTTP_200_OK)
            step_data = response_2.json()["step"]
            # we expect *no* data diff to be returned - otherwise you get an infinite
            # loop
            self.assertEqual(step_data["data"], {})

            textfield, editgrid = step_data["configuration"]["components"][0:2]
            self.assertTrue(textfield["hidden"])
            self.assertTrue(editgrid["hidden"])

    @tag("gh-5962")
    def test_clear_on_hide_behaviour_when_hiding_a_parent_uses_intermediate_cleared_values_for_other_rules(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "id": "trigger",
                        "key": "trigger",
                        "label": "Trigger",
                    },
                    {
                        "type": "fieldset",
                        "id": "fieldsetBeingHidden",
                        "key": "fieldsetBeingHidden",
                        "label": "Hidden fieldset",
                        "hidden": False,
                        "hideHeader": False,
                        "components": [
                            {
                                "type": "textfield",
                                "id": "textfield",
                                "key": "textfield",
                                "label": "Textfield",
                                "hidden": False,
                                "clearOnHide": True,
                                "defaultValue": "default",
                            },
                        ],
                    },
                    # used as observer of the second logic rule effect.
                    {
                        "type": "checkbox",
                        "id": "observer",
                        "key": "observer",
                        "label": "Observer",
                        "defaultValue": False,
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        rule1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "trigger"},
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "fieldsetBeingHidden",
                },
            ],
        )
        rule1.form_steps.set([form_step])
        rule2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "action": {"type": "variable", "value": True},
                    "variable": "observer",
                },
            ],
        )
        rule2.form_steps.set([form_step])
        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        self._add_submission_to_session(submission)
        # Assumes the initial state where:
        # * checkbox is unchecked
        # * user enters value in textfield
        # * user checks checkbox
        input_data = {
            "trigger": True,
            "textfield": "user input",
            "observer": False,
        }

        response = self.client.post(endpoint, data={"data": input_data})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        updated_configuration = response_data["step"]["configuration"]
        fieldset = updated_configuration["components"][1]
        self.assertTrue(fieldset["hidden"])
        self.assertFalse(fieldset["components"][0]["hidden"])
        data_updates = response_data["step"]["data"]
        self.assertEqual(data_updates, {"observer": True})

    @tag("gh-5962")
    def test_clear_on_hide_behaviour_applied_during_evaluation(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "id": "trigger",
                        "key": "trigger",
                        "label": "Trigger",
                    },
                    {
                        "type": "textfield",
                        "id": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "number",
                        "id": "number",
                        "key": "number",
                        "label": "Number",
                        "hidden": True,
                        "defaultValue": 67,
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        rule1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "trigger"},
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "textfield",
                },
            ],
        )
        rule1.form_steps.set([form_step])
        rule2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": False,
                    },
                    "component": "number",
                },
            ],
        )
        rule2.form_steps.set([form_step])
        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        self._add_submission_to_session(submission)
        input_data = {
            "trigger": True,
            "textfield": "clear-me",
        }

        response = self.client.post(endpoint, data={"data": input_data})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        updated_configuration = response_data["step"]["configuration"]
        textfield = updated_configuration["components"][1]
        self.assertTrue(textfield["hidden"])
        number = updated_configuration["components"][2]
        self.assertFalse(number["hidden"])
        data_updates = response_data["step"]["data"]
        # Number becomes visible, so the default value is set for it.
        self.assertEqual(data_updates, {"number": 67})

    @tag("gh-5962")
    def test_clear_on_hide_behaviour_hiding_a_parent_does_not_update_nested_field_data(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "id": "trigger",
                        "key": "trigger",
                        "label": "Trigger",
                    },
                    {
                        "type": "fieldset",
                        "id": "fieldsetBecomesHidden",
                        "key": "fieldsetBecomesHidden",
                        "label": "Hidden fieldset",
                        "hidden": False,
                        "hideHeader": False,
                        "components": [
                            {
                                "type": "textfield",
                                "id": "textfield",
                                "key": "textfield",
                                "label": "Textfield",
                            },
                        ],
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        rule1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "trigger"},
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "fieldsetBecomesHidden",
                },
            ],
        )
        rule1.form_steps.set([form_step])

        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        self._add_submission_to_session(submission)
        # because the parent is hidden, the renderer removed the `textfield` from the
        # input data due to its clearOnHide, leaving only the checkbox as input data
        input_data = {"trigger": True}

        response = self.client.post(endpoint, data={"data": input_data})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        updated_configuration = response_data["step"]["configuration"]
        fieldset = updated_configuration["components"][1]
        self.assertTrue(fieldset["hidden"])
        data_updates = response_data["step"]["data"]
        self.assertEqual(data_updates, {})

    def test_with_variable_of_future_step_in_trigger(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"}
                ],
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield2", "key": "Textfield 2", "label": "textfield2"}
                ],
            },
        )
        # Expected to trigger, because we are evaluating logic on the first step, so
        # the variable in the trigger is not available yet.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield2", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "action": {"type": "disable-next"},
                    "form_step_uuid": str(step_1.uuid),
                },
            ],
        )
        form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=form)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step_1.uuid},
        )
        self._add_submission_to_session(submission)

        response = self.client.post(endpoint, data={"data": {"textfield": "foo"}})

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(response.json()["step"]["canSubmit"])

    def test_clear_on_hide_behaviour_with_saved_step_data(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                        "hidden": True,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "observer",
                        "validate": {"required": False},
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        # Show the textfield
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "component": "textfield",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": False,
                    },
                }
            ],
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "component": "observer",
                    "action": {
                        "type": "property",
                        "property": {"value": "validate.required", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=form)
        # Simulate submitting a step: checkbox is True, so textfield was not hidden.
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"checkbox": True, "textfield": "foo", "observer": "bar"},
        )

        # Navigate back to the step and make the textfield hidden again.
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )
        response = self.client.post(
            logic_check_endpoint,
            {"data": {"checkbox": False, "textfield": "foo", "observer": "bar"}},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.json()
        observer = data["step"]["configuration"]["components"][2]
        self.assertTrue(observer["validate"]["required"])
        self.assertEqual({}, data["step"]["data"])

    def test_hidden_field_that_becomes_visible_properly_restores_value(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                        "hidden": True,
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "observer",
                        "validate": {"required": False},
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        # Show the textfield
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "component": "textfield",
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": False,
                    },
                }
            ],
        )
        # Expected to trigger: the value of the textfield will be reset (to the empty
        # component value) because of the above rule.
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": ["textfield", "not-in-context"]}, ""]},
            actions=[
                {
                    "component": "observer",
                    "action": {
                        "type": "property",
                        "property": {"value": "validate.required", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        form.apply_logic_analysis()

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
            logic_check_endpoint, {"data": {"checkbox": True, "observer": "foo"}}
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.json()
        observer = data["step"]["configuration"]["components"][2]
        self.assertTrue(observer["validate"]["required"])
        self.assertEqual({"textfield": ""}, data["step"]["data"])

    def test_hidden_field_by_frontend_added_to_post_data_anyway(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Textfield",
                        "conditional": {
                            "show": False,
                            "when": "checkbox",
                            "eq": True,
                        },
                        "clearOnHide": True,
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "observer",
                        "validate": {"required": False},
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [{"var": ["textfield", "not-in-context"]}, "not-in-context"]
            },
            actions=[
                {
                    "component": "observer",
                    "action": {
                        "type": "property",
                        "property": {"value": "validate.required", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        # Checkbox is True, so the textfield should not be in the data because of
        # conditional logic, but the user has spoofed the call to include it anyway.
        response = self.client.post(
            logic_check_endpoint,
            {
                "data": {
                    "checkbox": True,
                    "textfield": "some hacky data",
                    "observer": "foo",
                }
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.json()
        observer = data["step"]["configuration"]["components"][2]
        # The logic rule was triggered, which implies conditional logic was executed
        # to remove the textfield from the context.
        self.assertTrue(observer["validate"]["required"])
        self.assertEqual({}, data["step"]["data"])


@tag("gh-6005")
class MultipleRulesTargetingSameComponentVisibilityTests(SubmissionsMixin, APITestCase):
    def test_first_rule_triggers_second_does_not_must_not_clear_value(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "radio",
                        "label": "radio",
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "show-when-a",
                        "label": "show-when-a",
                        "hidden": True,
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "Observer",
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        # just a single rule does not reproduce the issue (!).
        # Rule 1: show the textfield when 'a' is selected in the radio
        show_textfield_action = {
            "formStep": None,
            "component": "show-when-a",
            "action": {
                "type": "property",
                "property": {"value": "hidden", "type": "bool"},
                "value": {},
                "state": False,
            },
        }
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "a"]},
            actions=[show_textfield_action],
        )
        # Rule 2: show the textfield when a non-sense value is selected in the radio
        # (never triggers!)
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "nonsense-value"]},
            actions=[show_textfield_action],
        )
        # Rule 3: expected to trigger, because the value should not be cleared
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "show-when-a"}, "do-not-clear-me"]},
            actions=[
                {
                    "action": {"type": "variable", "value": "foo"},
                    "variable": "observer",
                },
            ],
        )
        form.apply_logic_analysis()
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        # this assumes there has been a call before with `radio: a` that results in
        # show-when-a becoming visible, after which the user enters a value for that
        # field.
        response = self.client.post(
            logic_check_endpoint,
            {"data": {"radio": "a", "show-when-a": "do-not-clear-me", "observer": ""}},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertFalse(data["step"]["configuration"]["components"][1]["hidden"])
        self.assertEqual(data["step"]["data"], {"observer": "foo"})

    def test_second_rule_triggers_first_does_not_must_not_clear_value(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "radio",
                        "label": "radio",
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "show-when-a",
                        "label": "show-when-a",
                        "hidden": True,
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "Observer",
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()
        # just a single rule does not reproduce the issue (!).
        # Rule 1: show the textfield when a non-sense value is selected in the radio
        # (never triggers!)
        show_textfield_action = {
            "formStep": None,
            "component": "show-when-a",
            "action": {
                "type": "property",
                "property": {"value": "hidden", "type": "bool"},
                "value": {},
                "state": False,
            },
        }
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "nonsense-value"]},
            actions=[show_textfield_action],
        )
        # Rule 2: show the textfield when 'a' is selected in the radio
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "a"]},
            actions=[show_textfield_action],
        )
        # Rule 3: expected to trigger, because the value should not be cleared
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "show-when-a"}, "do-not-clear-me"]},
            actions=[
                {
                    "action": {"type": "variable", "value": "foo"},
                    "variable": "observer",
                },
            ],
        )
        form.apply_logic_analysis()
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
            logic_check_endpoint,
            {"data": {"radio": "a", "show-when-a": "do-not-clear-me", "observer": ""}},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertFalse(data["step"]["configuration"]["components"][1]["hidden"])
        self.assertEqual(data["step"]["data"], {"observer": "foo"})

    def test_rules_flip_from_hidden_to_visible_state_should_not_clear_value(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "radio",
                        "label": "radio",
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "textfield",
                        "key": "hide-when-a-but-show-when-checkbox-checked",
                        "label": "hide-when-a-but-show-when-checkbox-checked",
                        "hidden": False,
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "fieldset",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "nestedTextfield",
                                "label": "nestedTextfield",
                                "hidden": False,
                            }
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "observer",
                        "validate": {"required": False},
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        def _build_visibility_action(key: str, make_hidden: bool):
            return {
                "formStep": None,
                "component": key,
                "action": {
                    "type": "property",
                    "property": {"value": "hidden", "type": "bool"},
                    "value": {},
                    "state": make_hidden,
                },
            }

        # Hide (and clear) the textfield when 'a' is selected in the radio
        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "a"]},
            actions=[
                _build_visibility_action(
                    key="hide-when-a-but-show-when-checkbox-checked", make_hidden=True
                ),
                _build_visibility_action(key="fieldset", make_hidden=True),
            ],
        )
        # Expected to trigger: the value of the textfield gets cleared (meaning it gets
        # removed from the evaluation context entirely) because of the above rule.
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {
                        "var": [
                            "hide-when-a-but-show-when-checkbox-checked",
                            "not-in-context",
                        ]
                    },
                    "not-in-context",
                ]
            },
            actions=[
                {
                    "formStep": None,
                    "component": "observer",
                    "action": {
                        "type": "property",
                        "property": {"value": "validate.required", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                }
            ],
        )
        # Show the textfield when the checkbox is checked
        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "checkbox"},
            actions=[
                _build_visibility_action(
                    key="hide-when-a-but-show-when-checkbox-checked", make_hidden=False
                ),
                _build_visibility_action(key="fieldset", make_hidden=False),
            ],
        )
        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "hide-when-a-but-show-when-checkbox-checked"},
                    "do-not-clear-me",
                ]
            },
            actions=[
                {
                    "action": {"type": "variable", "value": "foo"},
                    "variable": "observer",
                },
            ],
        )
        # Deliberately do not use `form.apply_logic_analysis()` here, because it will
        # re-order the third logic rule to execute before the second one, which makes it
        # impossible to check the value after clearing.
        form_step.logic_rules.set([rule_1, rule_2, rule_3, rule_4])

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
            logic_check_endpoint,
            {
                "data": {
                    "radio": "a",
                    "checkbox": True,
                    "hide-when-a-but-show-when-checkbox-checked": "do-not-clear-me",
                    "nestedTextfield": "do-not-clear-me",
                    "observer": "",
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        with self.subTest("textfield"):
            textfield_component = data["step"]["configuration"]["components"][2]
            self.assertFalse(textfield_component["hidden"])

        with self.subTest("fieldset"):
            fieldset_component = data["step"]["configuration"]["components"][3]
            self.assertFalse(fieldset_component["hidden"])
            self.assertFalse(fieldset_component["components"][0]["hidden"])

        with self.subTest("observer"):
            observer_component = data["step"]["configuration"]["components"][4]
            self.assertTrue(observer_component["validate"]["required"])
            self.assertEqual(data["step"]["data"], {"observer": "foo"})

    def test_rules_flip_from_hidden_to_visible_state_should_not_clear_value_inverse(
        self,
    ):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "radio",
                        "label": "radio",
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                    {
                        "type": "checkbox",
                        "key": "checkbox",
                        "label": "checkbox",
                    },
                    {
                        "type": "textfield",
                        "key": "hide-when-a-but-show-when-checkbox-checked",
                        "label": "hide-when-a-but-show-when-checkbox-checked",
                        "hidden": True,
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "fieldset",
                        "hidden": True,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "nestedTextfield",
                                "label": "nestedTextfield",
                                "hidden": False,
                            }
                        ],
                    },
                    {
                        "type": "textfield",
                        "key": "observer",
                        "label": "observer",
                        "validate": {"required": False},
                    },
                ]
            },
        )
        form_step = form.formstep_set.get()

        def _build_visibility_action(key: str, make_hidden: bool):
            return {
                "formStep": None,
                "component": key,
                "action": {
                    "type": "property",
                    "property": {"value": "hidden", "type": "bool"},
                    "value": {},
                    "state": make_hidden,
                },
            }

        # Hide (and clear) the textfield when 'a' is selected in the radio
        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "radio"}, "a"]},
            actions=[
                _build_visibility_action(
                    key="hide-when-a-but-show-when-checkbox-checked", make_hidden=True
                ),
                _build_visibility_action(key="fieldset", make_hidden=True),
            ],
        )
        # Expected to trigger: the value of the textfield gets cleared (meaning it gets
        # removed from the evaluation context entirely) because of the above rule.
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {
                        "var": [
                            "hide-when-a-but-show-when-checkbox-checked",
                            "not-in-context",
                        ]
                    },
                    "not-in-context",
                ]
            },
            actions=[
                {
                    "formStep": None,
                    "component": "observer",
                    "action": {
                        "type": "property",
                        "property": {"value": "validate.required", "type": "bool"},
                        "value": {},
                        "state": True,
                    },
                }
            ],
        )
        # Show the textfield when the checkbox is checked
        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"var": "checkbox"},
            actions=[
                _build_visibility_action(
                    key="hide-when-a-but-show-when-checkbox-checked", make_hidden=False
                ),
                _build_visibility_action(key="fieldset", make_hidden=False),
            ],
        )
        rule_4 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "hide-when-a-but-show-when-checkbox-checked"},
                    "do-not-clear-me",
                ]
            },
            actions=[
                {
                    "action": {"type": "variable", "value": "foo"},
                    "variable": "observer",
                },
            ],
        )
        # Deliberately do not use `form.apply_logic_analysis()` here, because it will
        # re-order the third logic rule to execute before the second one, which makes it
        # impossible to check the value after clearing.
        form_step.logic_rules.set([rule_1, rule_2, rule_3, rule_4])

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
            logic_check_endpoint,
            {
                "data": {
                    "radio": "a",
                    "checkbox": True,
                    "hide-when-a-but-show-when-checkbox-checked": "do-not-clear-me",
                    "nestedTextfield": "do-not-clear-me",
                    "observer": "",
                }
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        with self.subTest("textfield"):
            textfield_component = data["step"]["configuration"]["components"][2]
            self.assertFalse(textfield_component["hidden"])

        with self.subTest("fieldset"):
            fieldset_component = data["step"]["configuration"]["components"][3]
            self.assertFalse(fieldset_component["hidden"])
            self.assertFalse(fieldset_component["components"][0]["hidden"])

        with self.subTest("observer"):
            observer_component = data["step"]["configuration"]["components"][4]
            self.assertTrue(observer_component["validate"]["required"])
            self.assertEqual(data["step"]["data"], {"observer": "foo"})


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
class EvaluateLogicSubmissionTest(SubmissionsMixin, APITestCase):
    def test_evaluate_logic_with_default_values(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "name",
                        "defaultValue": "some-default",
                    },
                    {
                        "type": "textfield",
                        "key": "optional",
                        "label": "optional",
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
        form.apply_logic_analysis()
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
        configuration = response.json()["configuration"]
        self.assertEqual(
            configuration["components"][1],
            {
                "key": "optional",
                "label": "optional",
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
                        "label": "number1",
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
                    "form_step_uuid": str(form.formstep_set.get().uuid),
                    "action": {"type": "disable-next"},
                }
            ],
        )
        form.apply_logic_analysis()
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
                        "label": "number1",
                    },
                    {
                        "type": "number",
                        "key": "number2",
                        "label": "number2",
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
        form.apply_logic_analysis()
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
