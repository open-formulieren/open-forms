import inspect

from django.test import TestCase

from glom import PathAccessError, glom

from openforms.formio.display.constants import OutputMode
from openforms.formio.display.elements import create_elements
from openforms.formio.display.registry import register
from openforms.formio.display.render import RenderContext, render_elements
from openforms.formio.display.wrap import get_submission_tree
from openforms.submissions.tests.factories import SubmissionFactory


class DisplayTests(TestCase):
    maxDiff = 1024 * 100

    def assertGlomEqual(self, obj, path, expected):
        try:
            value = glom(obj, path)
            self.assertEqual(value, expected)
        except PathAccessError as e:
            self.fail(str(e))

    def test_glom_equal(self):
        obj = {"a": {"b": 1, "c": [0, 1, 2]}}
        self.assertGlomEqual(obj, "a.b", 1)
        self.assertGlomEqual(obj, "a.c", [0, 1, 2])
        self.assertGlomEqual(obj, "a.c.0", 0)
        with self.assertRaises(AssertionError):
            self.assertGlomEqual(obj, "z", 1)
        with self.assertRaises(AssertionError):
            self.assertGlomEqual(obj, "a.b.0", 333)

    def test_simple_display(self):
        components = [
            {
                "key": "field1",
                "type": "textfield",
                "label": "My Field 1",
            },
            {
                "key": "field2",
                "type": "textfield",
                "label": "My Field 2",
            },
            {
                "key": "fieldset1",
                "type": "fieldset",
                "label": "My Fieldset Label",
                "components": [
                    {
                        "key": "nested1",
                        "type": "textfield",
                    },
                    {
                        "key": "nested2",
                        "type": "textfield",
                    },
                ],
            },
            {"key": "fieldsetEmpty", "type": "fieldset", "components": []},
        ]
        data = {
            "field1": "aaa",
            "field2": "bbb",
            "nested1": "n1",
            "nested2": "n2",
        }
        submission = SubmissionFactory.from_components(components, submitted_data=data)
        root = get_submission_tree(submission, register)

        self.assertGlomEqual(root, "children.0.component.key", "field1")
        self.assertGlomEqual(root, "children.0.plugin.identifier", "default")

        self.assertGlomEqual(root, "children.1.component.key", "field2")
        self.assertGlomEqual(root, "children.1.plugin.identifier", "default")

        self.assertGlomEqual(root, "children.2.component.key", "fieldset1")
        self.assertGlomEqual(root, "children.2.plugin.identifier", "fieldset")

        self.assertGlomEqual(root, "children.2.children.0.component.key", "nested1")
        self.assertGlomEqual(root, "children.2.children.1.component.key", "nested2")

        context = RenderContext(mode=OutputMode.summary, as_html=False)
        # result = list(root.create_elements(context))
        # expected = [
        #     LabelValueElem(label="Field1", value="aaa"),
        #     LabelValueElem(label="Field2", value="bbb"),
        #     HeaderElem(text="My Label"),
        #     LabelValueElem(label="nested1", value="n1"),
        #     LabelValueElem(label="nested2", value="n2"),
        # ]
        # self.assertEqual(result, expected)

        context = RenderContext(mode=OutputMode.summary, as_html=False)
        elements = create_elements(root.children, context)
        elements = list(elements)
        actual = render_elements(elements, context)

        print(elements)
        # result = root.render(mode=OutputMode.summary, as_html=False)

        expected = inspect.cleandoc(
            """
            My Field 1: aaa
            My Field 2: bbb
            My Fieldset Label
            nested1: n1
            nested2: n2
            """
        )

        self.assertEqual(actual, expected)

        context = RenderContext(mode=OutputMode.summary, as_html=True)
        elements = create_elements(root.children, context)
        elements = list(elements)
        actual = render_elements(elements, context)

        expected = inspect.cleandoc(
            """
            <tr>
            <td>My Field 1</td><td>aaa</td>
            </tr>
            <tr>
            <td>My Field 2</td><td>bbb</td>
            </tr>
            <tr>
            <td colspan="2"><h1>My Fieldset Label</h1><td>
            </tr>
            <tr>
            <td>nested1</td><td>n1</td>
            </tr>
            <tr>
            <td>nested2</td><td>n2</td>
            </tr>
            """
        )

        self.assertEqual(actual, expected)
