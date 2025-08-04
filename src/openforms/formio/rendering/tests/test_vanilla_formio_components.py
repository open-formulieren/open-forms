"""
Test the render component node implementations for the built-in Formio component types.

These can be considered integration tests for the Formio aspect, relying on the out
of the box configuration in Open Forms through the registry.
"""

from django.test import TestCase, override_settings

from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionStepFactory,
    TemporaryFileUploadFactory,
)

from ...typing import EditGridComponent
from ..nodes import ComponentNode


@override_settings(LANGUAGE_CODE="en")
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
                    # container: visible fieldset without visible children
                    {
                        "key": "fieldset1",
                        "type": "fieldset",
                        "label": "A container without visible children",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input1",
                                "label": "Input 1",
                                "hidden": True,
                            }
                        ],
                    },
                    # container: visible fieldset with visible children
                    {
                        "key": "fieldset2",
                        "type": "fieldset",
                        "label": "A container with visible children",
                        "hidden": False,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input2",
                                "label": "Input 2",
                                "hidden": True,
                            },
                            {
                                "type": "textfield",
                                "key": "input3",
                                "label": "Input 3",
                                "hidden": False,
                            },
                        ],
                    },
                    # container: hidden fieldset with 'visible' children
                    {
                        "key": "fieldset3",
                        "type": "fieldset",
                        "label": "A hidden container with visible children",
                        "hidden": True,
                        "components": [
                            {
                                "type": "textfield",
                                "key": "input4",
                                "label": "Input 4",
                                "hidden": False,
                            }
                        ],
                    },
                    # container: visible columns without visible children
                    {
                        "type": "columns",
                        "key": "columns1",
                        "label": "Columns 1",
                        "hidden": False,
                        "columns": [
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input5",
                                        "label": "Input 5",
                                        "hidden": True,
                                    }
                                ],
                            },
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input6",
                                        "label": "Input 6",
                                        "hidden": True,
                                    }
                                ],
                            },
                        ],
                    },
                    # container: visible columns with visible children
                    {
                        "type": "columns",
                        "key": "columns2",
                        "label": "Columns 2",
                        "hidden": False,
                        "columns": [
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input7",
                                        "label": "Input 7",
                                        "hidden": False,
                                    }
                                ],
                            },
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input8",
                                        "label": "Input 8",
                                        "hidden": True,
                                    }
                                ],
                            },
                        ],
                    },
                    # container: hidden columns with visible children
                    {
                        "type": "columns",
                        "key": "columns3",
                        "label": "Columns 3",
                        "hidden": True,
                        "columns": [
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input9",
                                        "label": "Input 9",
                                        "hidden": False,
                                    }
                                ],
                            },
                            {
                                "size": 6,
                                "components": [
                                    {
                                        "type": "textfield",
                                        "key": "input10",
                                        "label": "Input 10",
                                        "hidden": True,
                                    }
                                ],
                            },
                        ],
                    },
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
                "input6": "fffff",
                "input7": "ggggg",
                "input8": "hhhhh",
                "input9": "iiiii",
                "input10": "jjjjj",
            },
        )

        # expose test data to test methods
        cls.submission = submission
        cls.step = step

    def test_fieldsets_hidden_if_all_children_hidden(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][0]
        assert component["type"] == "fieldset"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertFalse(component_node.is_visible)
        self.assertEqual(list(component_node), [])

    def test_fieldsets_visible_if_any_child_visible(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][1]
        assert component["type"] == "fieldset"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertTrue(component_node.is_visible)
        nodelist = list(component_node)
        self.assertEqual(len(nodelist), 2)
        self.assertEqual(nodelist[0].label, "A container with visible children")
        self.assertEqual(nodelist[1].label, "Input 3")

    def test_fieldset_hidden_if_marked_as_such_and_visible_children(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][2]
        assert component["type"] == "fieldset"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertFalse(component_node.is_visible)
        self.assertEqual(list(component_node), [])

    def test_fieldset_with_hidden_label(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "A hidden label",
            "hidden": False,
            "hideHeader": True,
        }

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertEqual(component_node.label, "")

    def test_columns_hidden_if_all_children_hidden(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][3]
        assert component["type"] == "columns"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertFalse(component_node.is_visible)
        self.assertEqual(list(component_node), [])

    def test_columns_visible_if_any_child_visible(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][4]
        assert component["type"] == "columns"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertTrue(component_node.is_visible)
        nodelist = list(component_node)
        self.assertEqual(len(nodelist), 2)
        self.assertEqual(nodelist[0].component["label"], "Columns 2")
        self.assertEqual(nodelist[1].label, "Input 7")

    def test_column_hidden_if_marked_as_such_and_visible_children(self):
        # we always need a renderer instance
        renderer = Renderer(self.submission, mode=RenderModes.pdf, as_html=False)
        component = self.step.form_step.form_definition.configuration["components"][5]
        assert component["type"] == "columns"

        component_node = ComponentNode.build_node(
            step_data=self.step.data, component=component, renderer=renderer
        )

        self.assertFalse(component_node.is_visible)
        self.assertEqual(list(component_node), [])

    def test_columns_never_output_label(self):
        component = self.step.form_step.form_definition.configuration["components"][5]
        assert component["type"] == "columns"

        for render_mode in RenderModes.values:
            with self.subTest(render_mode=render_mode):
                renderer = Renderer(self.submission, mode=render_mode, as_html=False)

                component_node = ComponentNode.build_node(
                    step_data=self.step.data, component=component, renderer=renderer
                )

                self.assertEqual(component_node.label, "")
                self.assertIsNone(component_node.value)

    def test_wysiwyg_component_show_in_summary_enabled(self):
        """
        WYSIWYG is displayed in confirmation PDF, CLI rendering, and summary
        """
        component = {
            "type": "content",
            "key": "content",
            "html": "<p>WYSIWYG with <strong>markup</strong></p>",
            "input": False,
            "label": "Content",
            "hidden": False,
            "showInSummary": True,
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(form__name="public name"),
        )
        expected_visibility = {
            RenderModes.confirmation_email: False,
            RenderModes.pdf: True,
            RenderModes.cli: True,
            RenderModes.summary: True,
        }

        for render_mode, is_visible in expected_visibility.items():
            with self.subTest(render_mode=render_mode):
                renderer = Renderer(submission, mode=render_mode, as_html=False)
                component_node = ComponentNode.build_node(
                    step_data=step.data, component=component, renderer=renderer
                )

                self.assertEqual(component_node.is_visible, is_visible)

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.pdf, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )

            self.assertEqual(
                component_node.value, "<p>WYSIWYG with <strong>markup</strong></p>"
            )

        with self.subTest(as_html=False):
            renderer = Renderer(submission, mode=RenderModes.pdf, as_html=False)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )

            self.assertEqual(component_node.value, "WYSIWYG with markup")

    def test_wysiwyg_component_show_in_summary_disabled(self):
        """
        WYSIWYG is displayed in confirmation PDF and CLI rendering
        """
        component = {
            "type": "content",
            "key": "content",
            "html": "<p>WYSIWYG with <strong>markup</strong></p>",
            "input": False,
            "label": "Content",
            "hidden": False,
            "showInSummary": False,
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(form__name="public name"),
        )
        expected_visibility = {
            RenderModes.confirmation_email: False,
            RenderModes.pdf: True,
            RenderModes.cli: True,
            RenderModes.summary: False,
        }

        for render_mode, is_visible in expected_visibility.items():
            with self.subTest(render_mode=render_mode):
                renderer = Renderer(submission, mode=render_mode, as_html=False)
                component_node = ComponentNode.build_node(
                    step_data=step.data, component=component, renderer=renderer
                )

                self.assertEqual(component_node.is_visible, is_visible)

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.pdf, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )

            self.assertEqual(
                component_node.value, "<p>WYSIWYG with <strong>markup</strong></p>"
            )

        with self.subTest(as_html=False):
            renderer = Renderer(submission, mode=RenderModes.pdf, as_html=False)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )

            self.assertEqual(component_node.value, "WYSIWYG with markup")

    @override_settings(BASE_URL="http://localhost:8000")
    def test_file_component_email_registration(self):
        component = {
            "type": "file",
            "key": "file",
            "label": "My File",
            "hidden": False,
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )

        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "file": [
                    {
                        "data": {
                            "baseUrl": "http://localhost:8000/api/v2/",
                            "form": "",
                            "name": "blank.doc",
                            "project": "",
                            "size": 1048576,
                            "url": "http://localhost:8000/api/v2/submissions/files/35527900-8248-4e75-a553-c2d1039a002b",
                        },
                        "name": "blank-65faf10b-afaf-48af-a749-ff5780abf75b.doc",
                        "originalName": "blank.doc",
                        "size": 1048576,
                        "storage": "url",
                        "type": "application/msword",
                        "url": "http://localhost:8000/api/v2/submissions/files/35527900-8248-4e75-a553-c2d1039a002b",
                    }
                ]
            },
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="file",
            file_name="blank-renamed.doc",
            original_name="blank.doc",
            _component_configuration_path="components.0",
            _component_data_path="file",
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data,
                component=component,
                configuration_path="components.0",
                renderer=renderer,
            )

            link = component_node.render()
            self.assertTrue(link.startswith('My File: <a href="http://localhost:8000/'))
            self.assertTrue(
                link.endswith(
                    '" target="_blank" rel="noopener noreferrer">blank-renamed.doc</a>'
                )
            )

        with self.subTest(as_html=False):
            renderer = Renderer(
                submission, mode=RenderModes.registration, as_html=False
            )
            component_node = ComponentNode.build_node(
                step_data=step.data,
                component=component,
                configuration_path="components.0",
                renderer=renderer,
            )
            link = component_node.render()
            self.assertTrue(link.startswith("My File: http://localhost:8000/"))
            self.assertTrue(link.endswith(" (blank-renamed.doc)"))

    @override_settings(BASE_URL="http://localhost:8000")
    def test_nested_files(self):
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "label": "Files",
                "groupLabel": "File",
                "components": [
                    {
                        "type": "file",
                        "label": "File in repeating group",
                        "key": "fileInRepeatingGroup",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                        },
                    }
                ],
            },
            {
                "key": "nested.file",
                "type": "file",
                "registration": {
                    "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                },
            },
        ]
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": components},
        )

        upload_in_repeating_group_1, upload_in_repeating_group_2, nested_upload = (
            TemporaryFileUploadFactory.create_batch(3, submission=submission)
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "repeatingGroup": [
                    {
                        "fileInRepeatingGroup": [
                            {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                                "data": {
                                    "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                                    "form": "",
                                    "name": "my-image.jpg",
                                    "size": 46114,
                                    "baseUrl": "http://server",
                                    "project": "",
                                },
                                "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                                "size": 46114,
                                "type": "image/jpg",
                                "storage": "url",
                                "originalName": "my-image.jpg",
                            }
                        ]
                    },
                    {
                        "fileInRepeatingGroup": [
                            {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                                "data": {
                                    "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                                    "form": "",
                                    "name": "my-image.jpg",
                                    "size": 46114,
                                    "baseUrl": "http://server",
                                    "project": "",
                                },
                                "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                                "size": 46114,
                                "type": "image/jpg",
                                "storage": "url",
                                "originalName": "my-image.jpg",
                            }
                        ]
                    },
                ],
                "nested": {
                    "file": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
                                "form": "",
                                "name": "my-image.jpg",
                                "size": 46114,
                                "baseUrl": "http://server",
                                "project": "",
                            },
                            "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                            "size": 46114,
                            "type": "image/jpg",
                            "storage": "url",
                            "originalName": "my-image.jpg",
                        }
                    ],
                },
            },
        )
        # The factory creates a submission variable for the repeating group and for the nested file
        attachment1 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="repeatingGroup",
            file_name="file1.doc",
            original_name="file1.doc",
            _component_configuration_path="components.0.components.0",
            _component_data_path="repeatingGroup.0.fileInRepeatingGroup",
        )
        attachment2 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="repeatingGroup",
            file_name="file2.doc",
            original_name="file2.doc",
            _component_configuration_path="components.0.components.0",
            _component_data_path="repeatingGroup.1.fileInRepeatingGroup",
        )
        SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="nested.file",
            file_name="file3.doc",
            original_name="file3.doc",
            _component_configuration_path="components.1",
            _component_data_path="nested.file",
        )

        self.assertEqual(2, submission.submissionvaluevariable_set.count())
        self.assertTrue(
            submission.submissionvaluevariable_set.filter(key="repeatingGroup").exists()
        )
        self.assertTrue(
            submission.submissionvaluevariable_set.filter(key="nested.file").exists()
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            repeating_group_node = ComponentNode.build_node(
                step_data=step.data,
                component=components[0],
                renderer=renderer,
                configuration_path="components.0",
            )

            nodelist = list(repeating_group_node)

            # One node for the EditGrid, 2 nodes per child (2 children, since 2 files uploaded)
            self.assertEqual(5, len(nodelist))

            self.assertEqual("Files: ", nodelist[0].render())
            self.assertEqual("File 1", nodelist[1].render())

            link1 = nodelist[2].render()

            self.assertTrue(
                link1.startswith(
                    f'File in repeating group: <a href="http://localhost:8000/submissions/attachment/{attachment1.uuid}'
                )
            )
            self.assertTrue(
                link1.endswith(
                    'target="_blank" rel="noopener noreferrer">file1.doc</a>'
                )
            )
            self.assertEqual("File 2", nodelist[3].render())

            link2 = nodelist[4].render()

            self.assertTrue(
                link2.startswith(
                    f'File in repeating group: <a href="http://localhost:8000/submissions/attachment/{attachment2.uuid}'
                )
            )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            nested_file_node = ComponentNode.build_node(
                step_data=step.data,
                component=components[1],
                renderer=renderer,
                configuration_path="components.1",
            )

            link = nested_file_node.render()
            self.assertTrue(
                link.startswith(
                    'nested.file: <a href="http://localhost:8000/submissions/attachment/'
                )
            )
            self.assertTrue(
                link.endswith(
                    '" target="_blank" rel="noopener noreferrer">file3.doc</a>'
                )
            )

    @override_settings(BASE_URL="http://localhost:8000")
    def test_nested_files_with_duplicate_keys(self):
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "label": "Files",
                "groupLabel": "File",
                "components": [
                    {
                        "type": "file",
                        "label": "File in repeating group",
                        "key": "attachment",
                    }
                ],
            },
            {
                "key": "attachment",
                "type": "file",
            },
        ]
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": components},
        )

        upload_1, upload_2 = TemporaryFileUploadFactory.create_batch(
            2, submission=submission
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "repeatingGroup": [
                    {
                        "attachment": [
                            {
                                "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
                                "data": {
                                    "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
                                    "form": "",
                                    "name": "attachmentInside.pdf",
                                    "size": 46114,
                                    "baseUrl": "http://server",
                                    "project": "",
                                },
                                "name": "attachmentInside.pdf",
                                "size": 46114,
                                "type": "image/jpg",
                                "storage": "url",
                                "originalName": "attachmentInside.pdf",
                            }
                        ]
                    }
                ],
                "attachment": [
                    {
                        "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
                        "data": {
                            "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
                            "form": "",
                            "name": "attachmentOutside.pdf",
                            "size": 46114,
                            "baseUrl": "http://server",
                            "project": "",
                        },
                        "name": "attachmentOutside.pdf",
                        "size": 46114,
                        "type": "image/jpg",
                        "storage": "url",
                        "originalName": "attachmentOutside.pdf",
                    }
                ],
            },
        )
        # The factory creates a submission variable for the repeating group and for the nested file
        attachment1 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="repeatingGroup",
            file_name="attachmentInside.pdf",
            original_name="attachmentInside.pdf",
            _component_configuration_path="components.0.components.0",
            _component_data_path="repeatingGroup.0.attachment",
        )
        attachment2 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="attachment",
            file_name="attachmentOutside.pdf",
            original_name="attachmentOutside.pdf",
            _component_configuration_path="components.1",
            _component_data_path="attachment",
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            repeating_group_node = ComponentNode.build_node(
                step_data=step.data,
                component=components[0],
                configuration_path="components.0",
                renderer=renderer,
            )

            nodelist = list(repeating_group_node)

            # One node for the EditGrid, 2 nodes per child (1 child)
            self.assertEqual(3, len(nodelist))

            self.assertEqual("Files: ", nodelist[0].render())
            self.assertEqual("File 1", nodelist[1].render())

            link1 = nodelist[2].render()

            self.assertTrue(
                link1.startswith(
                    f'File in repeating group: <a href="http://localhost:8000/submissions/attachment/{attachment1.uuid}'
                )
            )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            outside_file_node = ComponentNode.build_node(
                step_data=step.data,
                component=components[1],
                configuration_path="components.1",
                renderer=renderer,
            )

            link = outside_file_node.render()
            self.assertTrue(
                link.startswith(
                    f'attachment: <a href="http://localhost:8000/submissions/attachment/{attachment2.uuid}'
                )
            )
            self.assertTrue(
                link.endswith(
                    '" target="_blank" rel="noopener noreferrer">attachmentOutside.pdf</a>'
                )
            )

    @override_settings(BASE_URL="http://localhost:8000")
    def test_two_different_files_in_repeating_group(self):
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "label": "Files",
                "groupLabel": "Group file",
                "components": [
                    {
                        "type": "file",
                        "label": "File 1 in repeating group",
                        "key": "fileInRepeatingGroup1",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                        },
                    },
                    {
                        "type": "file",
                        "label": "File 2 in repeating group",
                        "key": "fileInRepeatingGroup2",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/456-456-456"
                        },
                    },
                ],
            },
        ]
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": components},
        )

        upload_in_repeating_group_1, upload_in_repeating_group_2 = (
            TemporaryFileUploadFactory.create_batch(2, submission=submission)
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "repeatingGroup": [
                    {
                        "fileInRepeatingGroup1": [
                            {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                                "data": {
                                    "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                                    "form": "",
                                    "name": "my-image.jpg",
                                    "size": 46114,
                                    "baseUrl": "http://server",
                                    "project": "",
                                },
                                "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                                "size": 46114,
                                "type": "image/jpg",
                                "storage": "url",
                                "originalName": "my-image.jpg",
                            }
                        ],
                        "fileInRepeatingGroup2": [
                            {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                                "data": {
                                    "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                                    "form": "",
                                    "name": "my-image.jpg",
                                    "size": 46114,
                                    "baseUrl": "http://server",
                                    "project": "",
                                },
                                "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                                "size": 46114,
                                "type": "image/jpg",
                                "storage": "url",
                                "originalName": "my-image.jpg",
                            }
                        ],
                    },
                ],
            },
        )
        # The factory creates a submission variable for the repeating group and for the nested file
        attachment_1 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="repeatingGroup",
            file_name="file1.doc",
            original_name="file1.doc",
            _component_configuration_path="components.0.components.0",
            _component_data_path="repeatingGroup.0.fileInRepeatingGroup1",
        )
        attachment_2 = SubmissionFileAttachmentFactory.create(
            submission_step=step,
            form_key="repeatingGroup",
            file_name="file2.doc",
            original_name="file2.doc",
            _component_configuration_path="components.0.components.1",
            _component_data_path="repeatingGroup.0.fileInRepeatingGroup2",
        )

        self.assertEqual(1, submission.submissionvaluevariable_set.count())
        self.assertTrue(
            submission.submissionvaluevariable_set.filter(key="repeatingGroup").exists()
        )

        renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
        repeating_group_node = ComponentNode.build_node(
            step_data=step.data,
            component=components[0],
            configuration_path="components.0",
            renderer=renderer,
        )

        nodelist = list(repeating_group_node)

        # One node for the EditGrid, 3 nodes per child (1 child)
        self.assertEqual(4, len(nodelist))

        self.assertEqual("Files: ", nodelist[0].render())
        self.assertEqual("Group file 1", nodelist[1].render())

        link1 = nodelist[2].render()

        self.assertTrue(
            link1.startswith(
                f'File 1 in repeating group: <a href="http://localhost:8000/submissions/attachment/{attachment_1.uuid}'
            )
        )

        link2 = nodelist[3].render()

        self.assertTrue(
            link2.startswith(
                f'File 2 in repeating group: <a href="http://localhost:8000/submissions/attachment/{attachment_2.uuid}'
            )
        )

    def test_file_component_email_registration_no_file(self):
        # via GH issue #1594
        component = {
            "type": "file",
            "key": "file",
            "label": "My File",
            "hidden": False,
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={},
        )
        renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
        component_node = ComponentNode.build_node(
            step_data=step.data, component=component, renderer=renderer
        )
        link = component_node.render()
        self.assertEqual(link, "My File: ")

    def test_simple_editgrid(self):
        component = {
            "type": "editgrid",
            "key": "children",
            "label": "Children",
            "groupLabel": "Child",
            "hidden": False,
            "components": [
                {"key": "name", "type": "textfield", "label": "Name"},
                {"key": "surname", "type": "textfield", "label": "Surname"},
            ],
        }
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form, form_definition__configuration={"components": [component]}
        )
        submission = SubmissionFactory.create(
            form=form,
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "children": [
                    {"name": "John", "surname": "Doe"},
                    {"name": "Jane", "surname": "Doe"},
                ]
            },
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )
            nodelist = list(component_node)

            # One node for the EditGrid, 2 nodes per child (2 children)
            self.assertEqual(7, len(nodelist))

            self.assertEqual("Children: ", nodelist[0].render())
            self.assertEqual("Child 1", nodelist[1].render())
            self.assertEqual("Name: John", nodelist[2].render())
            self.assertEqual("Surname: Doe", nodelist[3].render())
            self.assertEqual("Child 2", nodelist[4].render())
            self.assertEqual("Name: Jane", nodelist[5].render())
            self.assertEqual("Surname: Doe", nodelist[6].render())

    def test_simple_editgrid_no_group_label(self):
        component = {
            "type": "editgrid",
            "key": "children",
            "label": "Children",
            "hidden": False,
            "components": [
                {"key": "name", "type": "textfield", "label": "Name"},
                {"key": "surname", "type": "textfield", "label": "Surname"},
            ],
        }
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form, form_definition__configuration={"components": [component]}
        )
        submission = SubmissionFactory.create(
            form=form,
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "children": [
                    {"name": "John", "surname": "Doe"},
                    {"name": "Jane", "surname": "Doe"},
                ]
            },
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )
            nodelist = list(component_node)

            # One node for the EditGrid, 2 nodes per child (2 children)
            self.assertEqual(7, len(nodelist))

            self.assertEqual("Item 1", nodelist[1].render())
            self.assertEqual("Item 2", nodelist[4].render())

    def test_editgrid_with_nested_fields(self):
        component = {
            "type": "editgrid",
            "key": "children",
            "label": "Children",
            "groupLabel": "Child",
            "hidden": False,
            "components": [
                {
                    "key": "personalDetails",
                    "type": "fieldset",
                    "label": "Personal Details",
                    "components": [
                        {"key": "name", "type": "textfield", "label": "Name"},
                        {"key": "surname", "type": "textfield", "label": "Surname"},
                    ],
                },
                {
                    "type": "columns",
                    "key": "columnsA",
                    "label": "Columns A",
                    "hidden": False,
                    "columns": [
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "inputA",
                                    "label": "Input A",
                                    "hidden": False,
                                }
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "inputB",
                                    "label": "Input B",
                                    "hidden": False,
                                }
                            ],
                        },
                    ],
                },
            ],
        }
        form_step = FormStepFactory.create(
            form_definition__configuration={"components": [component]}
        )
        submission = SubmissionFactory.create(
            form=form_step.form,
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "children": [
                    {"name": "John", "surname": "Doe", "inputA": "A1", "inputB": "B1"},
                    {"name": "Jane", "surname": "Doe", "inputA": "A2", "inputB": "B2"},
                ]
            },
        )

        with self.subTest(as_html=True):
            renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
            component_node = ComponentNode.build_node(
                step_data=step.data, component=component, renderer=renderer
            )
            nodelist = list(component_node)

            # One node for the EditGrid, 7 nodes per child (2 children)
            self.assertEqual(15, len(nodelist))

            self.assertEqual("Children: ", nodelist[0].render())

            self.assertEqual("Child 1", nodelist[1].render())
            self.assertEqual("Personal Details", nodelist[2].render())
            self.assertEqual("Name: John", nodelist[3].render())
            self.assertEqual("Surname: Doe", nodelist[4].render())
            self.assertEqual("Columns A", nodelist[5].component["label"])
            self.assertEqual("Input A: A1", nodelist[6].render())
            self.assertEqual("Input B: B1", nodelist[7].render())

            self.assertEqual("Child 2", nodelist[8].render())
            self.assertEqual("Personal Details", nodelist[9].render())
            self.assertEqual("Name: Jane", nodelist[10].render())
            self.assertEqual("Surname: Doe", nodelist[11].render())
            self.assertEqual("Columns A", nodelist[12].component["label"])
            self.assertEqual("Input A: A2", nodelist[13].render())
            self.assertEqual("Input B: B2", nodelist[14].render())

    def test_nested_editgrid_with_date_and_time_components(self):
        component: EditGridComponent = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Editgrid",
            "groupLabel": "Child",
            "hidden": False,
            "components": [
                {"key": "date", "type": "date", "label": "Date"},
                {"key": "time", "type": "time", "label": "Time"},
                {"key": "datetime", "type": "datetime", "label": "Datetime"},
                {
                    "key": "nestedEditgrid",
                    "type": "editgrid",
                    "label": "Nested editgrid",
                    "groupLabel": "Nested child",
                    "components": [
                        {
                            "key": "nestedDate",
                            "type": "date",
                            "label": "Nested date",
                            "multiple": True,
                        }
                    ],
                },
            ],
        }
        submission = SubmissionFactory.from_components(
            components_list=[component],
            submitted_data={
                "editgrid": [
                    {
                        "date": "2000-01-01",
                        "time": "12:34:56",
                        "datetime": "2000-01-01T12:34:56Z",
                        "nestedEditgrid": [
                            {"nestedDate": ["2001-02-03", "1999-12-31"]},
                        ],
                    },
                ]
            },
        )

        renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
        component_node = ComponentNode.build_node(
            step_data=submission.data, component=component, renderer=renderer
        )
        nodelist = list(component_node)

        self.assertEqual(8, len(nodelist))

        self.assertEqual("Editgrid: ", nodelist[0].render())
        self.assertEqual("Child 1", nodelist[1].render())
        self.assertEqual("Date: Jan. 1, 2000", nodelist[2].render())
        self.assertEqual("Time: 12:34 p.m.", nodelist[3].render())
        self.assertEqual("Datetime: Jan. 1, 2000 12:34", nodelist[4].render())
        self.assertEqual("Nested editgrid: ", nodelist[5].render())
        self.assertEqual("Nested child 1", nodelist[6].render())
        self.assertEqual(
            "Nested date: <ul><li>Feb. 3, 2001</li><li>Dec. 31, 1999</li></ul>",
            nodelist[7].render(),
        )

    def test_fieldset_with_logic_depending_on_selectboxes(self):
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldSet1",
                        "conditional": {
                            "show": True,
                            "when": "selectBoxes1",
                            "eq": "a",
                        },
                        "components": [
                            {
                                "key": "textField1",
                                "type": "textfield",
                            }
                        ],
                    },
                    {
                        "key": "selectBoxes1",
                        "type": "selectboxes",
                        "values": [
                            {"value": "a", "label": "A"},
                            {"value": "b", "label": "B"},
                        ],
                    },
                ]
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={"selectBoxes1": {"a": True, "b": False}, "textField1": "some data"},
        )

        renderer = Renderer(submission, mode=RenderModes.pdf, as_html=True)

        nodes = list(renderer)

        # Check that the fieldset is present
        # Nodes: Form, SubmissionStep, Fieldset, Component (textfield), Component (radio)
        self.assertEqual(len(nodes), 5)
