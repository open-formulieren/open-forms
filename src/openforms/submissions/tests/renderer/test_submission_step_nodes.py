from django.test import TestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ...rendering import Renderer, RenderModes
from ...rendering.nodes import SubmissionStepNode
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

    def test_visible(self):
        """
        Assert that the submission step node is visible without any logic evaluation.
        """
        modes = [
            RenderModes.pdf,
            RenderModes.confirmation_email,
            RenderModes.export,
        ]

        for sstep in [self.sstep1, self.sstep2]:
            for mode in modes:
                with self.subTest(
                    render_mode=mode, step=sstep.form_step.form_definition.name
                ):
                    renderer = Renderer(
                        submission=self.submission, mode=mode, as_html=False
                    )
                    node = SubmissionStepNode(renderer=renderer, step=sstep)

                    self.assertTrue(node.is_visible)

    def test_render_mode_pdf(self):
        renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=False
        )
        expected_output = {
            self.sstep1: "Step 1",
            self.sstep2: "Step 2",
        }

        for sstep, expected in expected_output.items():
            with self.subTest(step=sstep.form_step.form_definition.name):
                node = SubmissionStepNode(renderer=renderer, step=sstep)

                self.assertEqual(node.render(), expected)

    def test_render_mode_confirmation_email(self):
        renderer = Renderer(
            submission=self.submission,
            mode=RenderModes.confirmation_email,
            as_html=False,
        )
        expected_output = {
            self.sstep1: "Step 1",
            self.sstep2: "Step 2",
        }

        for sstep, expected in expected_output.items():
            with self.subTest(step=sstep.form_step.form_definition.name):
                node = SubmissionStepNode(renderer=renderer, step=sstep)

                self.assertEqual(node.render(), expected)

    def test_render_mode_export(self):
        renderer = Renderer(
            submission=self.submission, mode=RenderModes.export, as_html=False
        )
        expected_output = {
            self.sstep1: "",
            self.sstep2: "",
        }

        for sstep, expected in expected_output.items():
            with self.subTest(step=sstep.form_step.form_definition.name):
                node = SubmissionStepNode(renderer=renderer, step=sstep)

                self.assertEqual(node.render(), expected)

    def test_formio_child_nodes(self):
        """
        Assert that iterating over a SubmissionStepNode produces underlying formio
        components nodes.
        """
        # TODO!
        pass
