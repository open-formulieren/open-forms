from openforms.utils.tests.test_migrations import TestMigrations


class BackfillSubmissionAttachmentVariableMigrationTests(TestMigrations):
    migrate_from = "0060_auto_20220812_1439"
    migrate_to = "0061_backfill_submissionfileattachment_variable"
    app = "submissions"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormVariable = apps.get_model("forms", "FormVariable")

        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")
        SubmissionFileAttachment = apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )
        SubmissionValueVariable = apps.get_model(
            "submissions", "SubmissionValueVariable"
        )

        form = Form.objects.create(name="my-form")
        form_definition = FormDefinition.objects.create(
            name="my-definition",
            configuration={
                "components": [
                    # added for completeness as current implementation doesn't look at the configuration
                    {"type": "file", "key": "file-component-key"},
                    {"type": "text", "key": "extra-other-key"},
                ]
            },
        )
        form_step = FormStep.objects.create(
            form=form,
            form_definition=form_definition,
            order=1,
        )
        form_variable = FormVariable.objects.create(
            form=form,
            form_definition=form_definition,
            # we don't look at this so it doesn't match
            key="mismatching-key",
            source="component",
        )

        submission = Submission.objects.create(
            form=form,
        )
        submission_step = SubmissionStep.objects.create(
            submission=submission,
            form_step=form_step,
        )

        # setup the attachment and variable
        submission_attachment = SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            form_key="file-component-key",
            # expected to get backfilled
            submission_variable=None,
        )
        submission_variable = SubmissionValueVariable.objects.create(
            submission=submission,
            form_variable=form_variable,
            key="file-component-key",
        )

        # add some extra noise that is skipped/unrelevant
        form_variable_extra = FormVariable.objects.create(
            form=form,
            form_definition=form_definition,
            key="extra-other-key",
            source="component",
        )
        SubmissionValueVariable.objects.create(
            submission=submission,
            form_variable=form_variable_extra,
            key="extra-other-key",
        )

        self.submission_attachment_id = submission_attachment.id
        self.submission_variable_id = submission_variable.id

    def test_backfill_datamigration_sets_submission_variable_from_form_key(self):
        SubmissionFileAttachment = self.apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        attachment = SubmissionFileAttachment.objects.get(
            id=self.submission_attachment_id
        )

        self.assertIsNotNone(attachment.submission_variable)
        self.assertEqual(attachment.submission_variable.id, self.submission_variable_id)


class ReverseBackfillSubmissionAttachmentVariableMigrationTests(TestMigrations):
    # this tests the reverse migration of the above
    migrate_from = "0061_backfill_submissionfileattachment_variable"
    migrate_to = "0060_auto_20220812_1439"
    app = "submissions"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormVariable = apps.get_model("forms", "FormVariable")

        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")
        SubmissionFileAttachment = apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )
        SubmissionValueVariable = apps.get_model(
            "submissions", "SubmissionValueVariable"
        )

        form = Form.objects.create(name="my-form")
        form_definition = FormDefinition.objects.create(
            name="my-definition",
            configuration={
                "components": [
                    # added for completeness as current implementation doesn't look at the configuration
                    {"type": "file", "key": "file-component-key"},
                ]
            },
        )
        form_step = FormStep.objects.create(
            form=form,
            form_definition=form_definition,
            order=1,
        )
        form_variable = FormVariable.objects.create(
            form=form,
            form_definition=form_definition,
            # we don't look at this so it doesn't match
            key="mismatching-key",
            source="component",
        )

        submission = Submission.objects.create(
            form=form,
        )
        submission_step = SubmissionStep.objects.create(
            submission=submission,
            form_step=form_step,
        )

        # setup the attachment and variable
        submission_variable = SubmissionValueVariable.objects.create(
            submission=submission,
            form_variable=form_variable,
            key="file-component-key",
        )
        submission_attachment = SubmissionFileAttachment.objects.create(
            submission_step=submission_step,
            # expected to get reverse-backfilled
            form_key="",
            submission_variable=submission_variable,
        )

        self.submission_attachment_id = submission_attachment.id
        self.submission_variable_id = submission_variable.id

    def test_reverse_backfill_datamigration_restores_form_key(self):
        SubmissionFileAttachment = self.apps.get_model(
            "submissions", "SubmissionFileAttachment"
        )

        attachment = SubmissionFileAttachment.objects.get(
            id=self.submission_attachment_id
        )

        self.assertEqual(attachment.form_key, attachment.submission_variable.key)
