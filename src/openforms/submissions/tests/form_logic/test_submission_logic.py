from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ..factories import SubmissionFactory, SubmissionStepFactory
from ..mixins import SubmissionsMixin
from .factories import FormLogicFactory


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
