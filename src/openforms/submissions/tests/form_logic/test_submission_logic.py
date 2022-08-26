from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)
from openforms.logging.models import TimelineLogProxy

from ...form_logic import evaluate_form_logic
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
        form_step2_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": step2.uuid},
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
                    "form_step": f"http://example.com{form_step2_path}",
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
        form_step2_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": step2.uuid},
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
                    "form_step": f"http://example.com{form_step2_path}",
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
        form_step2_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": form_step2.uuid},
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
                    "form_step": f"http://example.com{form_step2_path}",
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
            response = self.client.post(
                endpoint, {"data": submission.get_merged_data()}
            )

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


class EvaluateLogicSubmissionTest(SubmissionsMixin, APITestCase):
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

    def test_evaluate_logic_log_event_triggered(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "firstname",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "date",
                        "key": "birthdate",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                ">": [{"date": {"var": "birthdate"}}, {"date": "2022-06-20"}]
            },
            actions=[
                {
                    "component": "firstname",
                    "formStep": "",
                    "action": {
                        "type": "property",
                        "property": {"value": "disabled", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "firstname": "foo",
                "birthdate": "2022-06-21",
            },
        )

        evaluate_form_logic(submission, submission_step, submission.get_merged_data())

        logs = TimelineLogProxy.objects.all()
        self.assertEqual(1, logs.count())
        log = logs[0]
        self.assertTrue(log.extra_data["evaluated_rules"][0]["trigger"])

    def test_evaluate_logic_log_event_not_triggered(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "firstname",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                    {
                        "type": "date",
                        "key": "birthdate",
                        "hidden": False,
                        "clearOnHide": True,
                    },
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                ">": [{"date": {"var": "birthdate"}}, {"date": "2022-06-20"}]
            },
            actions=[
                {
                    "component": "firstname",
                    "formStep": "",
                    "action": {
                        "type": "property",
                        "property": {"value": "disabled", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "firstname": "foo",
                "birthdate": "2022-06-19",
            },
        )

        evaluate_form_logic(submission, submission_step, submission.get_merged_data())

        logs = TimelineLogProxy.objects.all()
        self.assertEqual(1, logs.count())
        log = logs[0]
        self.assertFalse(log.extra_data["evaluated_rules"][0]["trigger"])
