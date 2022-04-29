from django.test import TestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ...rendering import Renderer, RenderModes
from ...rendering.nodes import FormNode, SubmissionStepNode
from ..factories import SubmissionFactory, SubmissionStepFactory


class FormNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create(
            name="public name",
            internal_name="internal name",
        )
        step1 = FormStepFactory.create(form=form, form_definition__name="Step 1")
        step2 = FormStepFactory.create(form=form, form_definition__name="Step 2")
        submission = SubmissionFactory.create(form=form)
        sstep1 = SubmissionStepFactory.create(submission=submission, form_step=step1)
        sstep2 = SubmissionStepFactory.create(submission=submission, form_step=step2)

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
