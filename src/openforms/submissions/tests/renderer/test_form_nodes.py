from django.test import TestCase

from ...rendering import Renderer, RenderModes
from ...rendering.nodes import FormNode
from ..factories import SubmissionFactory


class FormNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create(
            form__name="public name",
            form__internal_name="internal name",
        )

    def test_as_html_exposed(self):
        with self.subTest(as_html=False):
            renderer1 = Renderer(
                submission=self.submission, mode=RenderModes.pdf, as_html=False
            )
            node1 = FormNode(renderer=renderer1)

            self.assertFalse(node1.as_html)

        with self.subTest(as_html=True):
            renderer2 = Renderer(
                submission=self.submission, mode=RenderModes.pdf, as_html=True
            )
            node2 = FormNode(renderer=renderer2)

            self.assertTrue(node2.as_html)

    def test_visible(self):
        expected = {
            RenderModes.pdf: True,
            RenderModes.confirmation_email: True,
            RenderModes.export: False,
        }

        for mode, expected_visibility in expected.items():
            with self.subTest(render_mode=mode):
                renderer = Renderer(
                    submission=self.submission, mode=mode, as_html=False
                )
                node = FormNode(renderer=renderer)

                self.assertEqual(node.is_visible, expected_visibility)

    def test_render_modes(self):
        expected_output = {
            RenderModes.pdf: "public name",
            RenderModes.confirmation_email: "public name",
            RenderModes.export: "public name",
        }

        for mode, expected in expected_output.items():
            with self.subTest(render_mode=mode):
                renderer = Renderer(
                    submission=self.submission, mode=mode, as_html=False
                )
                node = FormNode(renderer=renderer)

                self.assertEqual(node.render(), expected)

    def test_no_children(self):
        modes = [RenderModes.pdf, RenderModes.confirmation_email, RenderModes.export]
        for mode in modes:
            with self.subTest(render_mode=mode):
                renderer = Renderer(
                    submission=self.submission, mode=mode, as_html=False
                )
                node = FormNode(renderer=renderer)

                children = list(node)

                self.assertEqual(children, [])
