from unittest.mock import patch

from django.test import TestCase

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..constants import RenderConfigurationOptions
from ..nodes import ComponentNode
from ..registry import Registry


class FormNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create(
            name="public name",
            internal_name="internal name",
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
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
                    # visible in PDF and confirmation email component, leaf node
                    {
                        "type": "textfield",
                        "key": "input3",
                        "label": "Input 3",
                        "hidden": False,
                        RenderConfigurationOptions.show_in_pdf: True,
                        RenderConfigurationOptions.show_in_confirmation_email: True,
                    },
                    # hidden in PDF and confirmation email component, leaf node
                    {
                        "type": "textfield",
                        "key": "input4",
                        "label": "Input 4",
                        "hidden": False,
                        RenderConfigurationOptions.show_in_pdf: False,
                        RenderConfigurationOptions.show_in_confirmation_email: False,
                    },
                    # visible in PDF and hidden in confirmation email component, leaf node
                    {
                        "type": "textfield",
                        "key": "input5",
                        "label": "Input 5",
                        "hidden": False,
                        RenderConfigurationOptions.show_in_pdf: True,
                        RenderConfigurationOptions.show_in_confirmation_email: False,
                    },
                    # hidden in PDF and visible in confirmation email component, leaf node
                    {
                        "type": "textfield",
                        "key": "input6",
                        "label": "Input 6",
                        "hidden": False,
                        RenderConfigurationOptions.show_in_pdf: False,
                        RenderConfigurationOptions.show_in_confirmation_email: True,
                    },
                    # container: visible fieldset without visible children
                    {
                        "type": "fieldset",
                        "label": "A container without visible children",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input7",
                                "label": "Input 7",
                                "hidden": True,
                            }
                        ],
                    },
                    # container: visible fieldset with visible children
                    {
                        "type": "fieldset",
                        "label": "A container with visible children",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input8",
                                "label": "Input 8",
                                "hidden": True,
                            },
                            {
                                "type": "textfield",
                                "key": "input9",
                                "label": "Input 9",
                                "hidden": False,
                            },
                        ],
                    },
                    # container: hidden fieldset with 'visible' children
                    {
                        "type": "fieldset",
                        "label": "A hidden container with visible children",
                        "hidden": True,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input10",
                                "label": "Input 10",
                                "hidden": False,
                            }
                        ],
                    },
                    # TODO container: columns
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form.formstep_set.get(),
            data={
                "input1": "aaaaa",
                "input2": "bbbbb",
                "input3": "ccccc",
                "input4": "ddddd",
                "input5": "eeeee",
                "input6": "fffff",
                "input7": "ggggg",
                "input8": "hhhhh",
                "input9": "iiiii",
            },
        )

        # expose test data to test methods
        cls.submission = submission
        cls.step = step

    def test_generic_node_builder(self):
        """
        Assert that ComponentNode.build_node produces node instances.
        """
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        # take a simple component
        component = self.step.form_step.form_definition.configuration["components"][0]
        assert component["key"] == "input1"

        component_node = ComponentNode.build_node(
            step=self.step, component=component, renderer=renderer
        )

        self.assertIsInstance(component_node, ComponentNode)
        self.assertEqual(component_node.depth, 0)
        self.assertTrue(component_node.is_visible)
        self.assertEqual(component_node.value, "aaaaa")
        self.assertEqual(component_node.display_value, "aaaaa")
        self.assertEqual(component_node.label, "Input 1")
        self.assertEqual(list(component_node.get_children()), [])
        nodelist = list(component_node)
        self.assertEqual(nodelist, [component_node])
        self.assertEqual(component_node.render(), "Input 1: aaaaa")

    def test_generic_node_builder_specific_subclasses(self):
        # set up mock registry and component class for test
        register = Registry()

        @register("textfield")
        class TextFieldNode(ComponentNode):
            pass

        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        # take a simple component
        component = self.step.form_step.form_definition.configuration["components"][0]
        assert component["key"] == "input1"

        with patch("openforms.formio.rendering.registry.register", new=register):
            component_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=renderer
            )

        self.assertIsInstance(component_node, TextFieldNode)

    def test_explicitly_hidden_component_skipped(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)

        with self.subTest("Simple hidden leaf component"):
            component = self.step.form_step.form_definition.configuration["components"][
                1
            ]
            assert component["key"] == "input2"
            assert component["hidden"]

            component_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=renderer
            )

            nodelist = list(component_node)

            self.assertEqual(nodelist, [])

        with self.subTest("Nested hidden component"):
            fieldset = self.step.form_step.form_definition.configuration["components"][
                6
            ]
            assert not fieldset["hidden"]

            # set up mock registry and component class for test
            register = Registry()

            with patch("openforms.formio.rendering.registry.register", new=register):
                component_node = ComponentNode.build_node(
                    step=self.step, component=fieldset, renderer=renderer
                )

                nodelist = list(component_node)

            self.assertEqual(len(nodelist), 1)
            self.assertEqual(nodelist[0].label, "A container without visible children")

    def test_export_always_emits_all_nodes(self):
        renderer = Renderer(self.submission, mode=RenderModes.export, as_html=False)

        nodelist = []
        for component in self.step.form_step.form_definition.configuration[
            "components"
        ]:
            component_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=renderer
            )
            nodelist += list(component_node)

        self.assertEqual(len(nodelist), 10)
        labels = [node.label for node in nodelist]
        self.assertEqual(
            labels,
            [
                "input1",
                "input2",
                "input3",
                "input4",
                "input5",
                "input6",
                "input7",
                "input8",
                "input9",
                "input10",
            ],
        )

    def test_render_mode_pdf(self):
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=True)
        # set up mock registry without special fieldset behaviour
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            for component in self.step.form_step.form_definition.configuration[
                "components"
            ]:
                component_node = ComponentNode.build_node(
                    step=self.step, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 6)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Input 1",
            "Input 3",
            "Input 5",
            "A container without visible children",
            "A container with visible children",
            "Input 9",
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
                    step=self.step, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 2)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Input 3",
            "Input 6",
        ]
        self.assertEqual(labels, expected_labels)
