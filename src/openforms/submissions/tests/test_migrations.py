from django_test_migrations.contrib.unittest_case import MigratorTestCase


class CreateMissingSubmissionStepsTests(MigratorTestCase):
    migrate_from = (
        "submissions",
        "0011_submissionstep_completed",
    )
    migrate_to = (
        "submissions",
        "0012_create_missing_submission_steps",
    )

    def prepare(self):
        apps = self.old_state.apps
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")

        # Form, form definitions, and form steps
        form = Form.objects.create(name="Form")
        fd_1 = FormDefinition.objects.create(
            name="fd_1",
            configuration={
                "components": [
                    {"type": "checkbox", "label": "Checkbox", "key": "checkbox"}
                ]
            },
        )
        step_1 = FormStep.objects.create(form=form, form_definition=fd_1, order=0)

        fd_2 = FormDefinition.objects.create(
            name="fd_2",
            configuration={
                "components": [
                    {"type": "textfield", "label": "Textfield", "key": "textfield"}
                ]
            },
        )
        FormStep.objects.create(
            slug="without-submission-step", form=form, form_definition=fd_2, order=1
        )

        fd_3 = FormDefinition.objects.create(
            name="fd_3",
            configuration={
                "components": [{"type": "number", "label": "Number", "key": "number"}]
            },
        )
        step_3 = FormStep.objects.create(form=form, form_definition=fd_3, order=2)

        # Submission and step
        submission = Submission.objects.create(form=form)
        SubmissionStep.objects.create(submission=submission, form_step=step_1)
        SubmissionStep.objects.create(submission=submission, form_step=step_3)

    def test_migration(self):
        """
        Ensure that the form step without a submission step has been created.
        """
        Submission = self.new_state.apps.get_model("submissions", "Submission")

        submission = Submission.objects.get()
        step_2 = submission.form.formstep_set.get(slug="without-submission-step")
        self.assertEqual(submission.submissionstep_set.count(), 3)
        self.assertTrue(submission.submissionstep_set.filter(form_step=step_2).exists())
