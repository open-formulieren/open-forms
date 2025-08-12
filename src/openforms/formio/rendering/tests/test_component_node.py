from unittest.mock import patch

from django.test import TestCase, tag

from openforms.formio.constants import DataSrcOptions
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import RenderConfigurationOptions
from ..nodes import ComponentNode
from ..registry import Registry
from ..structured import reshape_submission_data_for_json_summary


class ComponentNodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = {
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
                # visible in PDF, summary and confirmation email component, leaf node
                {
                    "type": "textfield",
                    "key": "input3",
                    "label": "Input 3",
                    "hidden": False,
                    RenderConfigurationOptions.show_in_pdf: True,
                    RenderConfigurationOptions.show_in_summary: True,
                    RenderConfigurationOptions.show_in_confirmation_email: True,
                },
                # hidden in PDF, summary and confirmation email component, leaf node
                {
                    "type": "textfield",
                    "key": "input4",
                    "label": "Input 4",
                    "hidden": False,
                    RenderConfigurationOptions.show_in_pdf: False,
                    RenderConfigurationOptions.show_in_summary: False,
                    RenderConfigurationOptions.show_in_confirmation_email: False,
                },
                # visible in PDF and summary and hidden in confirmation email component, leaf node
                {
                    "type": "textfield",
                    "key": "input5",
                    "label": "Input 5",
                    "hidden": False,
                    RenderConfigurationOptions.show_in_pdf: True,
                    RenderConfigurationOptions.show_in_summary: True,
                    RenderConfigurationOptions.show_in_confirmation_email: False,
                },
                # hidden in PDF and confirmation email component, visible in summary, leaf node
                {
                    "type": "textfield",
                    "key": "input5_1",
                    "label": "Input 5.1",
                    "hidden": False,
                    RenderConfigurationOptions.show_in_pdf: False,
                    RenderConfigurationOptions.show_in_summary: True,
                    RenderConfigurationOptions.show_in_confirmation_email: False,
                },
                # hidden in PDF and summary and visible in confirmation email component, leaf node
                {
                    "type": "textfield",
                    "key": "input6",
                    "label": "Input 6",
                    "hidden": False,
                    RenderConfigurationOptions.show_in_pdf: False,
                    RenderConfigurationOptions.show_in_summary: False,
                    RenderConfigurationOptions.show_in_confirmation_email: True,
                },
                # container: visible fieldset without visible children
                {
                    "type": "fieldset",
                    "key": "fieldsetNoVisibleChildren",
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
                    "key": "fieldsetVisibleChildren",
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
                    "key": "hiddenFieldsetVisibleChildren",
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
                # container: visible editgrid with visible children
                {
                    "type": "editgrid",
                    "key": "visibleEditGridWithVisibleChildren",
                    "label": "Visible editgrid with visible children",
                    "hidden": False,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input11",
                            "label": "Input 11",
                            "hidden": False,
                        }
                    ],
                },
                # container: hidden editgrid with visible children
                {
                    "type": "editgrid",
                    "key": "hiddenEditGridWithVisibleChildren",
                    "label": "Hidden editgrid with visible children",
                    "hidden": True,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input12",
                            "label": "Input 12",
                            "hidden": False,
                        }
                    ],
                },
                # container: visible editgrid with hidden children
                {
                    "type": "editgrid",
                    "key": "visibleEditGridWithHiddenChildren",
                    "label": "Visible editgrid with hidden children",
                    "hidden": False,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "input13",
                            "label": "Input 13",
                            "hidden": True,
                        }
                    ],
                },
                # hidden component, made visible by frontend logic, leaf node
                {
                    "key": "input14",
                    "type": "textfield",
                    "label": "Input 14",
                    "hidden": True,
                    "conditional": {
                        "show": True,
                        "when": "input1",
                        "eq": "aaaaa",
                    },
                },
                # visible component, made hidden by frontend logic, leaf node
                {
                    "key": "input15",
                    "type": "textfield",
                    "label": "Input 15",
                    "hidden": False,
                    "conditional": {
                        "show": False,
                        "when": "input1",
                        "eq": "aaaaa",
                    },
                },
                # TODO columns
                # soft required validation errors -> always ignored
                {
                    "key": "softRequiredErrors",
                    "type": "softRequiredErrors",
                    "html": "<p>I am hidden</p>",
                    "label": "Soft required errors",
                },
            ]
        }
        data = {
            "input1": "aaaaa",
            "input2": "bbbbb",
            "input3": "ccccc",
            "input4": "ddddd",
            "input5": "eeeee",
            "input5_1": "eeeee1",
            "input6": "fffff",
            "input7": "ggggg",
            "input8": "hhhhh",
            "input9": "iiiii",
            "visibleEditGridWithVisibleChildren": [
                {"input11": "kkkkk"},
                {"input11": "lllll"},
            ],
            "hiddenEditGridWithVisibleChildren": [
                {"input12": "mmmmm"},
                {"input12": "nnnnn"},
            ],
            "visibleEditGridWithHiddenChildren": [
                {"input13": "ooooo"},
                {"input13": "ppppp"},
            ],
            "input14": "qqqqq",
            "input15": "rrrrr",
        }

        submission = SubmissionFactory.from_components(
            components_list=config["components"], submitted_data=data
        )

        # expose test data to test methods
        cls.submission = submission
        cls.step = submission.steps[0]

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
            step_data=self.step.data, component=component, renderer=renderer
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
                step_data=self.step.data, component=component, renderer=renderer
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
                step_data=self.step.data, component=component, renderer=renderer
            )

            nodelist = list(component_node)

            self.assertEqual(nodelist, [])

        with self.subTest("Nested hidden component"):
            fieldset = self.step.form_step.form_definition.configuration["components"][
                7
            ]
            assert not fieldset["hidden"]

            # set up mock registry and component class for test
            register = Registry()

            with patch("openforms.formio.rendering.registry.register", new=register):
                component_node = ComponentNode.build_node(
                    step_data=self.step.data, component=fieldset, renderer=renderer
                )

                nodelist = list(component_node)

            self.assertEqual(len(nodelist), 1)
            self.assertEqual(nodelist[0].label, "A container without visible children")

    def test_explicitly_hidden_component_not_skipped_when_registration(self):
        # we always need a renderer instance
        renderer = Renderer(
            self.submission, mode=RenderModes.registration, as_html=False
        )

        with self.subTest("Simple hidden leaf component"):
            component = self.step.form_step.form_definition.configuration["components"][
                1
            ]
            assert component["key"] == "input2"
            assert component["hidden"]

            component_node = ComponentNode.build_node(
                step_data=self.step.data, component=component, renderer=renderer
            )

            nodelist = list(component_node)

            self.assertEqual(len(nodelist), 1)

        with self.subTest("Nested hidden component"):
            fieldset = self.step.form_step.form_definition.configuration["components"][
                7
            ]
            assert not fieldset["hidden"]

            # set up mock registry and component class for test
            register = Registry()

            with patch("openforms.formio.rendering.registry.register", new=register):
                component_node = ComponentNode.build_node(
                    step_data=self.step.data, component=fieldset, renderer=renderer
                )

                nodelist = list(component_node)

            self.assertEqual(len(nodelist), 2)
            self.assertEqual(nodelist[0].label, "A container without visible children")

    @tag("dh-673")
    def test_visible_component_inside_hidden_fieldset_not_skipped(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "fieldset",
                    "key": "fieldset",
                    "label": "Hidden fieldset",
                    "hidden": True,
                    "components": [
                        {
                            "type": "textfield",
                            "key": "textfield",
                            "label": "Text field",
                            "hidden": False,
                        },
                    ],
                }
            ],
        )

        rendered = reshape_submission_data_for_json_summary(submission)

        self.assertEqual(
            rendered,
            {
                submission.steps[0].form_step.slug: {
                    "fieldset": {
                        "textfield": "",
                    },
                }
            },
        )

    def test_export_always_emits_all_nodes(self):
        renderer = Renderer(self.submission, mode=RenderModes.export, as_html=False)

        nodelist = []
        for component in self.step.form_step.form_definition.configuration[
            "components"
        ]:
            component_node = ComponentNode.build_node(
                step_data=self.step.data, component=component, renderer=renderer
            )
            nodelist += list(component_node)

        self.assertEqual(len(nodelist), 16)
        labels = [node.label for node in nodelist]
        # The fieldset/editgrid components have no labels
        self.assertEqual(
            labels,
            [
                "input1",
                "input2",
                "input3",
                "input4",
                "input5",
                "input5_1",
                "input6",
                "input7",
                "input8",
                "input9",
                "input10",
                # edit grid must be treated as a leaf node instead of a layout node
                "visibleEditGridWithVisibleChildren",
                "hiddenEditGridWithVisibleChildren",
                "visibleEditGridWithHiddenChildren",
                "input14",
                "input15",
            ],
        )

    def test_render_mode_pdf(self):
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=True)
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

        self.assertEqual(len(nodelist), 11)
        labels = [node.label for node in nodelist]
        expected_labels = [
            "Input 1",
            "Input 3",
            "Input 5",
            "A container without visible children",
            "A container with visible children",
            "Input 9",
            "Visible editgrid with visible children",
            "Input 11",
            "Visible editgrid with hidden children",
            "Input 14",
            "Soft required errors",  # not actually rendered in full render mode
        ]
        self.assertEqual(labels, expected_labels)

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
            "Soft required errors",  # not actually rendered in full render mode
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

    def test_render_mode_pdf_with_list_values(self):
        config = {
            "components": [
                {
                    "type": "bsn",
                    "key": "bsn",
                    "label": "BSN",
                    "multiple": True,
                },
                {
                    "type": "date",
                    "key": "date",
                    "label": "Date",
                    "multiple": True,
                },
                {
                    "type": "datetime",
                    "key": "datetime",
                    "label": "DateTime",
                    "multiple": True,
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "multiple": True,
                },
                {
                    "type": "iban",
                    "key": "iban",
                    "label": "IBAN",
                    "multiple": True,
                },
                {
                    "type": "licenseplate",
                    "key": "licenseplate",
                    "label": "LicensePlate",
                    "multiple": True,
                },
                {
                    "type": "phoneNumber",
                    "key": "phoneNumber",
                    "label": "PhoneNumber",
                    "multiple": True,
                },
                {
                    "type": "postcode",
                    "key": "postcode",
                    "label": "Postcode",
                    "multiple": True,
                },
                {
                    "type": "textarea",
                    "key": "textarea",
                    "label": "Textarea",
                    "multiple": True,
                },
                {
                    "type": "time",
                    "key": "time",
                    "label": "Time",
                    "multiple": True,
                },
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
                        "dataSrc": DataSrcOptions.manual,
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
                        "dataSrc": DataSrcOptions.manual,
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
            "bsn": ["123456782", "987654321"],
            "date": ["2024-11-11", "2024-11-13", "2024-11-16"],
            "datetime": ["2022-09-08T12:00:00+02:00", "2022-10-08T15:00:00+02:00"],
            "email": ["foo@mail.com", "bar@mail.com"],
            "iban": ["RO09 BCYP 0000 0012 3456 7890", "RO09 BCYP 0000 0056 3456 7890"],
            "licenseplate": ["123-aa-1", "12-aa-31"],
            "phoneNumber": ["0612345678", "0645678923"],
            "postcode": ["1234aa", "5678bb"],
            "textarea": ["foo", "bar"],
            "time": ["12:12:00", "14:02:00", "19:21:00"],
            "selectboxes": {"option1": True, "option2": True},
            "radio": "option1",
            "select-single": "option1",
            "select-multiple": ["option2", "option3"],
            "textfield": ["Foo", "Bar"],
        }

        submission = SubmissionFactory.from_components(
            components_list=config["components"], submitted_data=data
        )
        step = submission.steps[0]
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            renderer = Renderer(submission, mode=RenderModes.pdf, as_html=True)
            for component in step.form_step.form_definition.configuration["components"]:
                component_node = ComponentNode.build_node(
                    step_data=step.data, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 15)

        expected = [
            ("BSN", "<ul><li>123456782</li><li>987654321</li></ul>"),
            (
                "Date",
                "<ul><li>11 november 2024</li><li>13 november 2024</li><li>16 november 2024</li></ul>",
            ),
            (
                "DateTime",
                "<ul><li>8 september 2022 12:00</li><li>8 oktober 2022 15:00</li></ul>",
            ),
            ("Email", "<ul><li>foo@mail.com</li><li>bar@mail.com</li></ul>"),
            (
                "IBAN",
                "<ul><li>RO09 BCYP 0000 0012 3456 7890</li><li>RO09 BCYP 0000 0056 3456 7890</li></ul>",
            ),
            ("LicensePlate", "<ul><li>123-aa-1</li><li>12-aa-31</li></ul>"),
            ("PhoneNumber", "<ul><li>0612345678</li><li>0645678923</li></ul>"),
            ("Postcode", "<ul><li>1234aa</li><li>5678bb</li></ul>"),
            ("Textarea", "<ul><li>foo</li><li>bar</li></ul>"),
            ("Time", "<ul><li>12:12</li><li>14:02</li><li>19:21</li></ul>"),
            ("Selectboxes", "<ul><li>Option 1</li><li>Option 2</li></ul>"),
            ("Radio", "Option 1"),
            ("Select single", "Option 1"),
            ("Select multiple", "<ul><li>Option 2</li><li>Option 3</li></ul>"),
            ("Textfield", "<ul><li>Foo</li><li>Bar</li></ul>"),
        ]
        values = [(node.label, node.display_value) for node in nodelist]
        self.assertEqual(values, expected)

    def test_render_mode_summary_with_list_values(self):
        config = {
            "components": [
                {
                    "type": "bsn",
                    "key": "bsn",
                    "label": "BSN",
                    "multiple": True,
                },
                {
                    "type": "date",
                    "key": "date",
                    "label": "Date",
                    "multiple": True,
                },
                {
                    "type": "datetime",
                    "key": "datetime",
                    "label": "DateTime",
                    "multiple": True,
                },
                {
                    "type": "email",
                    "key": "email",
                    "label": "Email",
                    "multiple": True,
                },
                {
                    "type": "iban",
                    "key": "iban",
                    "label": "IBAN",
                    "multiple": True,
                },
                {
                    "type": "licenseplate",
                    "key": "licenseplate",
                    "label": "LicensePlate",
                    "multiple": True,
                },
                {
                    "type": "phoneNumber",
                    "key": "phoneNumber",
                    "label": "PhoneNumber",
                    "multiple": True,
                },
                {
                    "type": "postcode",
                    "key": "postcode",
                    "label": "Postcode",
                    "multiple": True,
                },
                {
                    "type": "textarea",
                    "key": "textarea",
                    "label": "Textarea",
                    "multiple": True,
                },
                {
                    "type": "time",
                    "key": "time",
                    "label": "Time",
                    "multiple": True,
                },
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
                        "dataSrc": DataSrcOptions.manual,
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
                        "dataSrc": DataSrcOptions.manual,
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
            "bsn": ["123456782", "987654321"],
            "date": ["2024-11-11", "2024-11-13", "2024-11-16"],
            "datetime": ["2022-09-08T12:00:00+02:00", "2022-10-08T15:00:00+02:00"],
            "email": ["foo@mail.com", "bar@mail.com"],
            "iban": ["RO09 BCYP 0000 0012 3456 7890", "RO09 BCYP 0000 0056 3456 7890"],
            "licenseplate": ["123-aa-1", "12-aa-31"],
            "phoneNumber": ["0612345678", "0645678923"],
            "postcode": ["1234aa", "5678bb"],
            "textarea": ["foo", "bar"],
            "time": ["12:12:00", "14:02:00", "19:21:00"],
            "selectboxes": {"option1": True, "option2": True},
            "radio": "option1",
            "select-single": "option1",
            "select-multiple": ["option2", "option3"],
            "textfield": ["Foo", "Bar"],
        }

        submission = SubmissionFactory.from_components(
            components_list=config["components"], submitted_data=data
        )
        step = submission.steps[0]
        register = Registry()

        nodelist = []
        with patch("openforms.formio.rendering.registry.register", new=register):
            renderer = Renderer(submission, mode=RenderModes.summary, as_html=False)
            for component in step.form_step.form_definition.configuration["components"]:
                component_node = ComponentNode.build_node(
                    step_data=step.data, component=component, renderer=renderer
                )
                nodelist += list(component_node)

        self.assertEqual(len(nodelist), 15)

        expected = [
            ("BSN", "123456782; 987654321"),
            ("Date", "11 november 2024; 13 november 2024; 16 november 2024"),
            ("DateTime", "8 september 2022 12:00; 8 oktober 2022 15:00"),
            ("Email", "foo@mail.com; bar@mail.com"),
            ("IBAN", "RO09 BCYP 0000 0012 3456 7890; RO09 BCYP 0000 0056 3456 7890"),
            ("LicensePlate", "123-aa-1; 12-aa-31"),
            ("PhoneNumber", "0612345678; 0645678923"),
            ("Postcode", "1234aa; 5678bb"),
            ("Textarea", "foo; bar"),
            ("Time", "12:12; 14:02; 19:21"),
            ("Selectboxes", "Option 1; Option 2"),
            ("Radio", "Option 1"),
            ("Select single", "Option 1"),
            ("Select multiple", "Option 2; Option 3"),
            ("Textfield", "Foo; Bar"),
        ]
        values = [(node.label, node.display_value) for node in nodelist]
        self.assertEqual(values, expected)
