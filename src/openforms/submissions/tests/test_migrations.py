from collections import defaultdict

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from openforms.variables.constants import FormVariableDataTypes

FILE_BOILERPLATE = {
    "file": {"type": []},
    "filePattern": "",
}

# not relevant for the tests - we don't actually create any files or content, just make
# sure if this changes in the future, we have a single place to modify.
SUBMISSION_FILE_ATTACHMENT_BOILERPLATE = {
    "content": "",
    "file_name": "dummy.bin",
    "original_name": "dummy.bin",
    "content_type": "application/octet-stream",
}


class SubmissionFileAttachmentMetadataMigrationTests(MigratorTestCase):
    migrate_from = (
        "submissions",
        "0015_alter_submissionfileattachment_submission_variable_and_more",
    )
    migrate_to = (
        "submissions",
        "0017_convert_attachment_metadata",
    )
    maxDiff = None

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormVariable = apps.get_model("forms", "FormVariable")

        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")
        SubmissionValueVariable = apps.get_model(
            "submissions", "SubmissionValueVariable"
        )
        SubmissionFileAttachment = apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        # create a form that has file upload fields, in particular with more exotic
        # constructs (that are technically possible!)
        form = Form.objects.create(name="Form with file components")
        fd = FormDefinition.objects.create(
            name="FD with file components",
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "topLevel.file",
                        "label": "Top level file",
                        **FILE_BOILERPLATE,
                    },
                    {
                        "type": "columns",
                        "key": "columns",
                        "label": "Columns",
                        "columns": [
                            {
                                "size": 12,
                                "components": [
                                    {
                                        "type": "file",
                                        "key": "columnsFile",
                                        "label": "Columns file",
                                        **FILE_BOILERPLATE,
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "type": "file",
                                "key": "fieldsetFile",
                                "label": "Fieldset file",
                                **FILE_BOILERPLATE,
                            }
                        ],
                    },
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "groupLabel": "Item",
                        "components": [
                            {
                                "type": "editgrid",
                                "key": "nested.editgrid",
                                "label": "Nested editgrid",
                                "groupLabel": "Item",
                                "components": [
                                    {
                                        "type": "file",
                                        "key": "someParentinEditgrid.file",
                                        "label": "Nested Editgrid file",
                                        **FILE_BOILERPLATE,
                                    }
                                ],
                            }
                        ],
                    },
                ]
            },
        )
        form_step = FormStep.objects.create(form=form, form_definition=fd, order=0)
        FormVariable.objects.create_for_form(form)

        # create a submission, simulating a past submissions for the provided form.
        # NOTE: this can also contain snapshotted data for a form configuration that has
        # since been changed (!). That's covered in another test.
        submission = Submission.objects.create(form=form)
        submission_step = SubmissionStep.objects.create(
            submission=submission,
            form_step=form_step,
        )

        submission_variable_0 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="topLevel.file",
            value=[{"url": ""}, {"url": ""}],  # irrelevant for data migration
            configuration=fd.configuration["components"][0],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.object,
        )
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_0,
            # can in *theory* be blank for non-editgrid components, but in practice it
            # never is - test added to validate the data migration convers this.
            _component_data_path="",
            _component_configuration_path="components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )
        # second upload for the same field (!)
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_0,
            # can in *theory* be blank for non-editgrid components, but in practice it
            # never is
            _component_data_path="topLevel.file",
            _component_configuration_path="components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )

        # columns
        submission_variable_1 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="columnsFile",
            value=[{"url": ""}],  # irrelevant for data migration
            configuration=fd.configuration["components"][1]["columns"][0]["components"][
                0
            ],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.object,
        )
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_1,
            # can in *theory* be blank for non-editgrid components, but in practice it
            # never is
            _component_data_path="columnsFile",
            _component_configuration_path="components.1.columns.0.components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )

        # fieldset
        submission_variable_2 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="fieldsetFile",
            value=[{"url": ""}],  # irrelevant for data migration
            configuration=fd.configuration["components"][2]["components"][0],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.object,
        )
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_2,
            # can in *theory* be blank for non-editgrid components, but in practice it
            # never is
            _component_data_path="fieldsetFile",
            _component_configuration_path="components.2.components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )

        # editgrid
        submission_variable_3 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="editgrid",
            value=[
                {
                    "nested": {
                        "editgrid": [
                            {"someParentinEditgrid": {"file": []}},
                            {
                                "someParentinEditgrid": {
                                    "file": [
                                        # deliberately empty, value doesn't matter for data migration
                                        {"url": ""},
                                        {"url": ""},
                                    ]
                                }
                            },
                            # some fields could be absent due to conditional logic (!)
                            {},
                        ]
                    }
                },
                # some fields could be absent due to conditional logic (!)
                {"nested": {"editgrid": []}},
                {"nested": {"editgrid": [{}]}},
                {},
            ],
            configuration=fd.configuration["components"][3],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.editgrid,
        )
        # 0 files for: first item in top level edit grid, first item in nested editgrid
        # 2 files for: first item in top level edit grid, second item in nested editgrid
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_3,
            _component_data_path="editgrid.0.nested.editgrid.1.someParentinEditgrid.file",
            _component_configuration_path="components.3.components.0.components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_3,
            _component_data_path="editgrid.0.nested.editgrid.1.someParentinEditgrid.file",
            _component_configuration_path="components.3.components.0.components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )
        # 0 files for: first item in top level edit grid, third item in nested editgrid
        # 0 files for: second item in top level edit grid
        # 0 files for: third item in top level edit grid
        # 0 files for: fourth item in top level edit grid

    def test_file_component_metadata_converted_correctly(self):
        SubmissionFileAttachment = self.new_state.apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        attachments_by_component_key = defaultdict(list)
        for attachment in SubmissionFileAttachment.objects.order_by(
            "component_key", "_data_path", "pk"
        ):
            attachments_by_component_key[attachment.component_key].append(
                (
                    attachment.submission_variable.key,
                    attachment._data_path,
                )
            )

        expected_attachments_by_component_key = {
            "topLevel.file": [
                ("topLevel.file", "topLevel.file"),
                ("topLevel.file", "topLevel.file"),
            ],
            "columnsFile": [("columnsFile", "columnsFile")],
            "fieldsetFile": [("fieldsetFile", "fieldsetFile")],
            "someParentinEditgrid.file": [
                ("editgrid", "editgrid.0.nested.editgrid.1.someParentinEditgrid.file"),
                ("editgrid", "editgrid.0.nested.editgrid.1.someParentinEditgrid.file"),
            ],
        }

        self.assertEqual(
            attachments_by_component_key,
            expected_attachments_by_component_key,
        )


class SubmissionFileAttachmentMetadataMigrationEdgeCaseTests(MigratorTestCase):
    migrate_from = (
        "submissions",
        "0015_alter_submissionfileattachment_submission_variable_and_more",
    )
    migrate_to = (
        "submissions",
        "0017_convert_attachment_metadata",
    )
    maxDiff = None

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormVariable = apps.get_model("forms", "FormVariable")

        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")
        SubmissionValueVariable = apps.get_model(
            "submissions", "SubmissionValueVariable"
        )
        SubmissionFileAttachment = apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        # create a form that has file upload fields, in particular with more exotic
        # constructs (that are technically possible!)
        form = Form.objects.create(name="Form with file components")
        fd = FormDefinition.objects.create(
            name="FD with file components",
            configuration={
                "components": [
                    # will be removed from the FD after the attachment records are
                    # created.
                    {
                        "type": "file",
                        "key": "topLevel.file",
                        "label": "Top level file",
                        **FILE_BOILERPLATE,
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "Fieldset",
                        "components": [
                            {
                                "type": "editgrid",
                                "key": "editgrid",
                                "label": "Editgrid",
                                "groupLabel": "Item",
                                "components": [
                                    {
                                        "type": "file",
                                        "key": "fieldsetEditgridFile0",
                                        "label": "Editgrid file 1",
                                        **FILE_BOILERPLATE,
                                    },
                                    # will be removed from the FD after the attachment
                                    # records are created.
                                    {
                                        "type": "file",
                                        "key": "fieldsetEditgridFile1",
                                        "label": "Editgrid file 2",
                                        **FILE_BOILERPLATE,
                                    },
                                ],
                            },
                        ],
                    },
                ]
            },
        )
        form_step = FormStep.objects.create(form=form, form_definition=fd, order=0)
        FormVariable.objects.create_for_form(form)

        # create a submission, simulating a past submissions for the provided form.
        submission = Submission.objects.create(form=form)
        submission_step = SubmissionStep.objects.create(
            submission=submission,
            form_step=form_step,
        )

        # historical snapshot this component will be removed
        submission_variable_0 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="topLevel.file",
            value=[{"url": ""}],  # irrelevant for data migration
            configuration=fd.configuration["components"][0],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.object,
        )
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_0,
            # can in *theory* be blank for non-editgrid components, but in practice it
            # never is
            _component_data_path="topLevel.file",
            _component_configuration_path="components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )

        # fieldset with editgrid inside
        submission_variable_1 = SubmissionValueVariable.objects.create(
            submission=submission,
            key="editgrid",
            value=[
                {
                    "fieldsetEditgridFile0": [{"url": ""}],
                    "fieldsetEditgridFile1": [{"url": ""}],
                },
            ],  # file value itself is irrelevant for data migration
            configuration=fd.configuration["components"][1]["components"][0],
            data_type=FormVariableDataTypes.array,
            data_subtype=FormVariableDataTypes.editgrid,
        )
        # 1 file for the first file field in the first editgrid item
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_1,
            _component_data_path="editgrid.0.fieldsetEditgridFile0",
            _component_configuration_path="components.1.components.0components.0",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )
        # 1 file for the second file field in the first editgrid item
        SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            submission_variable=submission_variable_1,
            _component_data_path="editgrid.0.fieldsetEditgridFile1",
            _component_configuration_path="components.1.components.0components.1",
            **SUBMISSION_FILE_ATTACHMENT_BOILERPLATE,
        )

        # now update the formio definition *and* the form variables, simulating a form
        # edit/revision after a submission with uploads was made.
        fd.configuration["components"] = [
            # top level file removed
            {
                "type": "fieldset",
                "key": "fieldset",
                "label": "Fieldset",
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "groupLabel": "Item",
                        "components": [
                            {
                                "type": "file",
                                "key": "fieldsetEditgridFile0",
                                "label": "Editgrid file 1",
                                **FILE_BOILERPLATE,
                            },
                            # second file file in edit grid removed
                        ],
                    },
                ],
            },
        ]
        fd.save()
        FormVariable.objects.create_for_form(form)
        assert set(form.formvariable_set.values_list("key", flat=True)) == {"editgrid"}

    def test_file_component_metadata_conversion_robustness(self):
        SubmissionFileAttachment = self.new_state.apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        attachments_by_component_key = defaultdict(list)
        for attachment in SubmissionFileAttachment.objects.order_by(
            "component_key", "_data_path", "pk"
        ):
            attachments_by_component_key[attachment.component_key].append(
                (
                    attachment.submission_variable.key,
                    attachment._data_path,
                )
            )

        expected_attachments_by_component_key = {
            # components.0 is no longer the file component, but has become the editgrid.
            # that's not an issue for "regular" components, because we can use the
            # variable configuration snapshot
            "topLevel.file": [("topLevel.file", "topLevel.file")],
            # components.1 no longer exists, so these end up with an unresolvable
            # component/key
            "<UNKNOWN>": [
                ("editgrid", "editgrid.0.fieldsetEditgridFile0"),
                ("editgrid", "editgrid.0.fieldsetEditgridFile1"),
            ],
        }

        self.assertEqual(
            attachments_by_component_key,
            expected_attachments_by_component_key,
        )
