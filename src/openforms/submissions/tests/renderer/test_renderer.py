from django.test import TestCase

from rest_framework.reverse import reverse

from openforms.forms.constants import FormVariableSources
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

from ...rendering import Renderer, RenderModes
from ...rendering.nodes import FormNode, SubmissionStepNode
from ..factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)


class FormNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create(
            name="public name",
            internal_name="internal name",
        )
        step1 = FormStepFactory.create(
            form=form,
            form_definition__name="Step 1",
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "input1",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__name="Step 2",
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "input2",
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)
        sstep1 = SubmissionStepFactory.create(submission=submission, form_step=step1)
        sstep2 = SubmissionStepFactory.create(submission=submission, form_step=step2)
        SubmissionValueVariableFactory.create(
            key="ud1",
            value="Some data 1",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=True,
            form_variable__show_in_pdf=True,
            form_variable__show_in_summary=True,
        )
        SubmissionValueVariableFactory.create(
            key="ud2",
            value="Some data 2",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=False,
            form_variable__show_in_pdf=False,
            form_variable__show_in_summary=False,
        )

        # expose test data to test methods
        cls.submission = submission
        cls.sstep1 = sstep1
        cls.sstep2 = sstep2

    def test_renderer_build_nodelist(self):
        renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

        nodes = [
            node
            for node in renderer
            if isinstance(node, (FormNode, SubmissionStepNode))
        ]

        self.assertEqual(len(nodes), 3)
        rendered = [node.render() for node in nodes]
        self.assertEqual(rendered, ["public name", "Step 1", "Step 2"])

    def test_renderer_with_form_logic_and_disabled_step(self):
        # set up logic
        form = self.submission.form
        form_step2_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": self.sstep2.form_step.uuid},
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "input1"}, "disabled-step-2"]},
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
        # set up data that marks step as not-applicable
        self.sstep1.data = {"input1": "disabled-step-2"}
        self.sstep1.save()

        renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

        nodes = [
            node
            for node in renderer
            if isinstance(node, (FormNode, SubmissionStepNode))
        ]

        self.assertEqual(len(nodes), 2)
        enabled_step_node = nodes[1]
        self.assertEqual(enabled_step_node.step, self.sstep1)

    def test_performance_num_queries(self):
        """
        Assert that the number of queries stays low while rendering a submission.
        """
        renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

        # Expected queries:
        # 1. Retrieve all the variables defined for the submission form
        # 2. Retrieve all the submission variable values
        # 3. Getting the submission steps for the given submission
        # 4. Get the step-specific data from submission variable values (TODO: this can probably be optimized away?)
        # 5. Load submission state: get form steps
        # 6. Load submission state: get submission steps
        # 7. Query the form logic rules for the submission form (and this is cached)
        # 8. Query if there are user defined variables
        with self.assertNumQueries(8):
            list(renderer)
