from itertools import product

from django.test import TestCase

from openforms.formio.display.constants import OutputMode
from openforms.formio.display.elements import Header, LabelValue, create_elements
from openforms.formio.display.registry import register
from openforms.formio.display.render import RenderContext, render_elements
from openforms.formio.display.wrap import get_submission_tree
from openforms.submissions.tests.factories import SubmissionFactory


class MatrixTestBase(TestCase):
    def run_matrix(self, components, data, matrix):
        submission = SubmissionFactory.from_components(components, submitted_data=data)
        root = get_submission_tree(submission, register)

        for mode, as_html, expected in matrix:
            context = RenderContext(
                mode=mode,
                as_html=as_html,
            )
            elements = list(create_elements(root.children, context))
            results = list(render_elements(elements, context))
            # TODO how test?
            for i, (elem, result, (elem_type, expected)) in enumerate(
                zip(elements, results, expected)
            ):
                with self.subTest(mode=mode, as_html=as_html, i=i):
                    self.assertIsInstance(elem, elem_type)
                    self.assertEqual(result, expected)

    def generate_matrix(self, modes, as_html, expected):
        if not isinstance(modes, (tuple, list)):
            modes = [modes]
        if not isinstance(as_html, (tuple, list)):
            as_html = [as_html]

        matrix = list()
        for mode, as_html in product(modes, as_html):
            matrix.append((mode, as_html, expected))
        return matrix


class CommonFieldTests(MatrixTestBase):
    def test_currency_uses_formatter(self):
        components = [
            {
                "type": "currency",
                "key": "component1",
                "label": "My Field",
            }
        ]
        data = {"component1": 1234.5}
        matrix = [
            (
                OutputMode.summary,
                False,
                [
                    (LabelValue, "My Field: 1.234,50"),
                ],
            ),
            (
                OutputMode.summary,
                True,
                [
                    (LabelValue, "My Field: 1.234,50"),
                ],
            ),
        ]
        self.run_matrix(components, data, matrix)

    def test_textfield_as_generic_default(self):
        components = [
            {
                "type": "textfield",
                "key": "component1",
                "label": "My Field",
            }
        ]
        data = {"component1": "foo & bar"}
        matrix = [
            (
                OutputMode.summary,
                False,
                [
                    LabelValue("My Field", "foo & bar"),
                ],
            ),
            (
                OutputMode.summary,
                True,
                [
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
            (
                OutputMode.pdf,
                False,
                [
                    LabelValue("My Field", "foo & bar"),
                ],
            ),
            (
                OutputMode.pdf,
                True,
                [
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
            (
                OutputMode.email_confirmation,
                False,
                [
                    LabelValue("My Field", "foo & bar"),
                ],
            ),
            (
                OutputMode.email_confirmation,
                True,
                [
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
        ]
        matrix = self.generate_matrix(
            OutputMode.all(),
            True,
            [
                LabelValue("My Field", "foo &amp; bar"),
            ],
        )
        self.run_matrix(components, data, matrix)

        matrix = self.generate_matrix(
            OutputMode.all(),
            False,
            [
                LabelValue("My Field", "foo & bar"),
            ],
        )
        self.run_matrix(components, data, matrix)


class FieldsetTests(MatrixTestBase):
    def test_empty(self):
        components = [
            {
                "type": "fieldset",
                "key": "component1",
                "label": "My Fieldset",
                "components": [],
            }
        ]
        data = {}
        matrix = [
            (
                OutputMode.summary,
                False,
                [],
            ),
            (
                OutputMode.pdf,
                False,
                [],
            ),
            (
                OutputMode.email_confirmation,
                False,
                [],
            ),
        ]
        self.run_matrix(components, data, matrix)

    def test_visible_content(self):
        components = [
            {
                "type": "fieldset",
                "key": "component1",
                "label": "My Fieldset",
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "My Field",
                    }
                ],
            }
        ]
        data = {
            "component1": "foo & bar",
        }
        matrix = [
            (
                OutputMode.summary,
                True,
                [
                    Header(text="My Fieldset"),
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
            (
                OutputMode.pdf,
                True,
                [
                    Header(text="My Fieldset"),
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
            (
                OutputMode.email_confirmation,
                True,
                [
                    Header(text="My Fieldset"),
                    LabelValue("My Field", "foo &amp; bar"),
                ],
            ),
        ]
        self.run_matrix(components, data, matrix)

    def test_empty_hide_label(self):
        components = [
            {
                "type": "fieldset",
                "key": "component1",
                "label": "My Fieldset",
                "components": [],
                "hideLabel": True,
            }
        ]
        data = {}
        matrix = [
            (
                OutputMode.summary,
                False,
                [],
            ),
            (
                OutputMode.pdf,
                False,
                [],
            ),
            (
                OutputMode.email_confirmation,
                False,
                [],
            ),
        ]
        self.run_matrix(components, data, matrix)
