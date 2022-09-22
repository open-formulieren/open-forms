from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin

COMPONENTS_1 = [
    # visible component, leaf node
    {
        "type": "textfield",
        "key": "input1",
        "label": "Input 1",
        "hidden": False,
    },
    # hidden component, leaf node
    {
        "type": "textfield",
        "key": "input2",
        "label": "Input 2",
        "hidden": True,
    },
]


COMPONENTS_2 = [  # container: visible fieldset with visible children
    {
        "type": "fieldset",
        "key": "fieldsetVisibleChildren",
        "label": "A container with visible children",
        "hidden": False,
        "components": [
            {
                "type": "textfield",
                "key": "input3",
                "label": "Input 3",
                "hidden": True,
            },
            {
                "type": "textfield",
                "key": "input4",
                "label": "Input 4",
                "hidden": False,
            },
        ],
    },
    # container: hidden fieldset with visible children
    {
        "type": "fieldset",
        "key": "hiddenFieldsetVisibleChildren",
        "label": "A hidden container with visible children",
        "hidden": True,
        "components": [
            {
                "type": "textfield",
                "key": "input5",
                "label": "Input 5",
                "hidden": True,
            },
            {
                "type": "textfield",
                "key": "input6",
                "label": "Input 6",
                "hidden": False,
            },
        ],
    },
]


class SubmissionSummaryRendererTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={"components": COMPONENTS_1},
            form_definition__slug="fd-0",
            form_definition__name="Form Definition 0",
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={"components": COMPONENTS_2},
            form_definition__slug="fd-1",
            form_definition__name="Form Definition 1",
        )

        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={
                "input1": "first input",
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
            data={
                "input2": "second input",
                "input4": "fourth input",
            },
        )

        cls.submission = submission

    def test_get_data_summary_page(self):
        data = self.submission.render_summary_page()

        self.assertEqual(2, len(data))

        step1, step2 = data

        self.assertEqual("fd-0", step1["slug"])
        self.assertEqual("Form Definition 0", step1["name"])
        self.assertEqual(1, len(step1["data"]))  # input1
        self.assertIn("name", step1["data"][0])
        self.assertIn("value", step1["data"][0])
        self.assertIn("component", step1["data"][0])

        self.assertEqual("fd-1", step2["slug"])
        self.assertEqual("Form Definition 1", step2["name"])
        self.assertEqual(2, len(step2["data"]))  # fieldsetVisibleChildren and input3
        self.assertIn("name", step2["data"][0])
        self.assertIn("value", step2["data"][0])
        self.assertIn("component", step2["data"][0])

    def test_check_summary_renderer_queries(self):
        """Make sure we are not making a query to retrieve the form definition for each step"""

        # 1. Get form steps
        # 2. Get submission steps
        # 3. Get form variables
        # 4. Get submission variables
        # 5. Get form logic
        # 6. Get auth info
        with self.assertNumQueries(6):
            self.submission.render_summary_page()


class SubmissionCompletionTests(SubmissionsMixin, APITestCase):
    def test_summary_page_endpoint(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={"components": COMPONENTS_1},
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={"components": COMPONENTS_2},
        )

        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={
                "input1": "first input",
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
            data={
                "input2": "second input",
                "input4": "fourth input",
            },
        )

        self._add_submission_to_session(submission)

        url = reverse("api:submission-summary", kwargs={"uuid": submission.uuid})
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertEqual(2, len(data))
