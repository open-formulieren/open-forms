from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

from ..factories import SubmissionFactory, SubmissionStepFactory
from ..mixins import SubmissionsMixin


class SideEffectTests(SubmissionsMixin, APITestCase):
    def test_not_applicable_steps_are_reset(self):
        """
        Assert that subsequent steps are reset when they become not-applicable.
        """
        # set up the form with logic
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "radio",
                        "key": "step1",
                        "label": "step1",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
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
                        "key": "step2",
                        "label": "step2",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "step1"},
                    "a",
                ]
            },
            actions=[
                {
                    "form_step_uuid": f"{step2.uuid}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": LogicActionTypes.step_not_applicable,
                    },
                }
            ],
        )

        # set up a submission
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"step1": "b"},  # With this data, step 2 is applicable
        )
        # mimick step 2 being submitted as well
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"step2": "submitted"},
        )
        # check internal state for correct test setup
        step1_url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step1.uuid},
        )
        step2_url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step2.uuid},
        )
        with self.subTest("Test setup check"):
            step2_detail = self.client.get(step2_url)

            self.assertTrue(step2_detail.data["is_applicable"])

        # now alter the data of step one, triggering the N/A logic
        with self.subTest("Modify step 1 data to trigger logic"):
            step1_detail = self.client.get(step1_url)

            response = self.client.put(
                step1_url,
                {
                    **step1_detail.json(),
                    "data": {"step1": "a"},
                },
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the state of step 2 again
        with self.subTest("Verify step 2 state"):
            step2_detail = self.client.get(step2_url)

            self.assertFalse(step2_detail.data["is_applicable"])
            self.assertEqual(step2_detail.data["data"], {})

    def test_blocked_submission_is_reset(self):
        """
        Assert that subsequent steps are reset when they become not-applicable.
        """
        # set up the form with logic
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "fieldA",
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
                        "key": "fieldB",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "fieldA"},
                    {"var": "fieldB"},
                ]
            },
            actions=[
                {"form_step_uuid": str(step2.uuid), "action": {"type": "disable-next"}}
            ],
            trigger_from_step=step2,
        )

        # set up a submission
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"fieldA": "B"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"fieldB": "B"},
        )
        # check internal state for correct test setup
        logic_check_endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step2.uuid},
        )

        response = self.client.post(
            logic_check_endpoint, data={"data": {"fieldB": "A"}}
        )

        data = response.json()

        self.assertTrue(data["step"]["canSubmit"])
