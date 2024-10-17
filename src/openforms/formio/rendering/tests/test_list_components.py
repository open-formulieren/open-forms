from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import SubmissionFactory

from ..default import ChoicesNode, SelectNode, TextNode
from ..nodes import ComponentNode
from ..registry import Registry


class FormNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = {
            "components": [
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "label": "Selectboxes",
                    "values": [
                        {
                            "value": "option1",
                            "label": "Option 1",
                        },
                        {
                            "value": "option2",
                            "label": "Option 2",
                        },
                        {
                            "value": "option3",
                            "label": "Option 3",
                        },
                    ],
                },
                {
                    "type": "radio",
                    "key": "radio",
                    "label": "Radio",
                    "values": [
                        {
                            "value": "option1",
                            "label": "Option 1",
                        },
                        {
                            "value": "option2",
                            "label": "Option 2",
                        },
                    ],
                },
                {
                    "type": "select",
                    "key": "select-single",
                    "label": "Select single",
                    "multiple": False,
                    "openForms": {
                        "dataSrc": "manual",
                    },
                    "data": {
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ]
                    },
                },
                {
                    "type": "select",
                    "key": "select-multiple",
                    "label": "Select multiple",
                    "multiple": True,
                    "openForms": {
                        "dataSrc": "manual",
                    },
                    "data": {
                        "values": [
                            {
                                "label": "Option 1",
                                "value": "option1",
                            },
                            {
                                "label": "Option 2",
                                "value": "option2",
                            },
                            {
                                "label": "Option 3",
                                "value": "option3",
                            },
                        ]
                    },
                },
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Textfield",
                    "multiple": True,
                },
            ]
        }
        data = {
            "selectboxes": {"option1": True, "option2": True},
            "radio": "option1",
            "select-single": "option1",
            "select-multiple": ["option2", "option3"],
            "textfield": ["Foo", "Bar"],
        }

        submission = SubmissionFactory.from_components(
            components_list=config["components"], submitted_data=data
        )

        # expose test data to test methods
        cls.submission = submission
        cls.step = submission.steps[0]

    def test_render_mode_pdf(self):
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=True)
        # set up mock registry without special fieldset/editgrid behaviour
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            for component in self.step.form_step.form_definition.configuration[
                "components"
            ]:
                if component["type"] == "selectboxes" or component["type"] == "radio":
                    component_node = ChoicesNode(
                        step_data=self.step.data, component=component, renderer=renderer
                    )
                elif component["type"] == "select":
                    component_node = SelectNode(
                        step_data=self.step.data, component=component, renderer=renderer
                    )
                elif component["type"] == "textfield":
                    component_node = TextNode(
                        step_data=self.step.data, component=component, renderer=renderer
                    )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 5)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Selectboxes",
            "Radio",
            "Select single",
            "Select multiple",
            "Textfield",
        ]
        self.assertEqual(labels, expected_labels)

        values = [node.value_list for node in nodelist]
        expected_values = [
            ["Option 1", "Option 2"],
            "Option 1",
            ["Option 1"],
            ["Option 2", "Option 3"],
            ["Foo", "Bar"],
        ]
        self.assertEqual(values, expected_values)

    def test_render_mode_summary(self):
        # NOTE the summary renders as text but some like the 'content' component render html
        renderer = Renderer(self.submission, mode=RenderModes.summary, as_html=False)
        # set up mock registry without special fieldset/editgrid behaviour
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            for component in self.step.form_step.form_definition.configuration[
                "components"
            ]:
                component_node = ComponentNode.build_node(
                    step_data=self.step.data, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        # self.assertEqual(len(nodelist), 11)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Input 1",
            "Input 3",
            "Input 5",
            "Input 5.1",
            "A container without visible children",
            "A container with visible children",
            "Input 9",
            "Visible editgrid with visible children",
            "Input 11",
            "Visible editgrid with hidden children",
            "Input 14",
        ]
        self.assertEqual(labels, expected_labels)

    def test_render_mode_confirmation_email(self):
        renderer = Renderer(
            self.submission, mode=RenderModes.confirmation_email, as_html=True
        )
        # set up mock registry without special fieldset behaviour
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            for component in self.step.form_step.form_definition.configuration[
                "components"
            ]:
                component_node = ComponentNode.build_node(
                    step_data=self.step.data, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 2)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Input 3",
            "Input 6",
        ]
        self.assertEqual(labels, expected_labels)
