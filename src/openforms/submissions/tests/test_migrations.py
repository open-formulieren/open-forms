from openforms.submissions.constants import SubmissionValueVariableSources
from openforms.utils.tests.test_migrations import TestMigrations


class CoSignDataVersionMigrationTests(TestMigrations):
    app = "submissions"
    migrate_from = "0003_alter_submissionvaluevariable_unique_together_and_more"
    migrate_to = "0004_set_co_sign_data_version"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        Submission = apps.get_model("submissions", "Submission")
        form = Form.objects.create(name="test")

        no_co_sign_data = Submission.objects.create(form=form)
        self.pk_no_co_sign_data = no_co_sign_data.pk
        v1_co_sign_data = Submission.objects.create(
            form=form,
            co_sign_data={
                "plugin": "demo",
                "identifier": "1234",
                "representation": "J. Doe, 1234",
                "co_sign_auth_attribute": "employee_id",
                "fields": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                },
            },
        )
        self.pk_v1_co_sign_data = v1_co_sign_data.pk
        v2_co_sign_data = Submission.objects.create(
            form=form,
            co_sign_data={
                "plugin": "demo",
                "attribute": "employee_id",
                "value": "1234",
                "cosign_date": "2025-01-01T00:00:00Z",
            },
        )
        self.pk_v2_co_sign_data = v2_co_sign_data.pk

    def test_version_key_added_only_when_relevant(self):
        Submission = self.apps.get_model("submissions", "Submission")

        no_co_sign_data = Submission.objects.get(pk=self.pk_no_co_sign_data)

        self.assertEqual(no_co_sign_data.co_sign_data, {})

    def test_correct_version_key_added_based_on_shape(self):
        Submission = self.apps.get_model("submissions", "Submission")

        with self.subTest(version="v1"):
            v1_co_sign_data = Submission.objects.get(pk=self.pk_v1_co_sign_data)

            self.assertEqual(
                v1_co_sign_data.co_sign_data,
                {
                    "version": "v1",
                    "plugin": "demo",
                    "identifier": "1234",
                    "representation": "J. Doe, 1234",
                    "co_sign_auth_attribute": "employee_id",
                    "fields": {
                        "first_name": "Jane",
                        "last_name": "Doe",
                    },
                },
            )

        with self.subTest(version="v2"):
            v2_co_sign_data = Submission.objects.get(pk=self.pk_v2_co_sign_data)

            self.assertEqual(
                v2_co_sign_data.co_sign_data,
                {
                    "version": "v2",
                    "plugin": "demo",
                    "attribute": "employee_id",
                    "value": "1234",
                    "cosign_date": "2025-01-01T00:00:00Z",
                },
            )


class SubmissionValueVariableConfigurationMigrationTests(TestMigrations):
    app = "submissions"
    migrate_from = "0006_submissionvaluevariable_configuration"
    migrate_to = "0007_add_configuration_to_existing_submission_value_variables"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        Submission = apps.get_model("submissions", "Submission")
        SubmissionStep = apps.get_model("submissions", "SubmissionStep")
        SubmissionValueVariable = apps.get_model(
            "submissions", "SubmissionValueVariable"
        )

        form = Form.objects.create(name="test")

        # Step 1
        self.form_def_1_configuration = {
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield_1",
                },
                {
                    "type": "editgrid",
                    "key": "editgrid",
                    "label": "Editgrid",
                    "components": [
                        {"key": "date", "type": "date", "label": "Date"},
                        {"key": "time", "type": "time", "label": "Time"},
                    ],
                },
            ]
        }
        form_def_1 = FormDefinition.objects.create(
            name="Definition 1", configuration=self.form_def_1_configuration
        )
        form_step_1 = FormStep.objects.create(
            form=form, form_definition=form_def_1, order=0
        )

        # Step 2
        self.form_def_2_configuration = {
            "components": [{"type": "textfield", "key": "textfield_2"}]
        }
        form_def_2 = FormDefinition.objects.create(
            name="Definition 2", configuration=self.form_def_2_configuration
        )
        form_step_2 = FormStep.objects.create(
            form=form, form_definition=form_def_2, order=0
        )

        submission = Submission.objects.create(form=form)
        SubmissionStep.objects.create(submission=submission, form_step=form_step_1)

        SubmissionValueVariable.objects.create(
            submission=submission,
            key="textfield_1",
            value="Foo",
            source=SubmissionValueVariableSources.user_input,
            configuration={},
        )
        SubmissionValueVariable.objects.create(
            submission=submission,
            key="editgrid",
            value=[
                {
                    "date": "2000-01-01",
                    "time": "12:34:56",
                }
            ],
            source=SubmissionValueVariableSources.user_input,
            configuration={},
        )

        SubmissionStep.objects.create(submission=submission, form_step=form_step_2)
        SubmissionValueVariable.objects.create(
            submission=submission,
            key="textfield_2",
            value="Bar",
            source=SubmissionValueVariableSources.user_input,
            configuration={},
        )


        SubmissionStep.objects.create(
            submission=submission,
            form_step=None,
            form_step_history={
                "form_step": {
                    "pk": 3,
                    "model": "forms.formstep",
                    "fields": {
                        "form": 1,
                        "form_definition": 3,
                        "slug": "foo",
                        "uuid": "0ca5e188-1f09-4233-96e0-273bffbb257f",
                        "order": 0,
                    },
                },
                "form_definition": {
                    "pk": 3,
                    "model": "forms.formdefinition",
                    "fields": {
                        "name": "Definition 3",
                        "slug": "definition-3",
                        "uuid": "e339b98c-ce9f-4300-a2b9-0145f3aa3823",
                        "configuration": {
                            "components": [
                                {
                                    "key": "textfield_3",
                                    "type": "textfield",
                                    "label": "Textfield 3",
                                }
                            ],
                        },
                        "_num_components": 1,
                    },
                },
            },
        )

    def test_empty_configuration_updated(self):
        SubmissionValueVariable = self.apps.get_model(
            "submissions", "SubmissionValueVariable"
        )

        self.assertEqual(SubmissionValueVariable.objects.count(), 4)

        # Variables in step 1
        var = SubmissionValueVariable.objects.get(key="textfield_1")
        self.assertEqual(var.configuration, self.form_def_1_configuration)

        var = SubmissionValueVariable.objects.get(key="editgrid")
        self.assertEqual(var.configuration, self.form_def_1_configuration)

        # Variable in step 2
        var = SubmissionValueVariable.objects.get(key="textfield_2")
        self.assertEqual(var.configuration, self.form_def_2_configuration)

        # Variable in step 3 with deleted form step
        var = SubmissionValueVariable.objects.get(key="textfield_3")
        self.assertEqual(
            var.configuration,
            self.form_def_2_configuration,
            {
                "components": [
                    {
                        "key": "textfield_3",
                        "type": "textfield",
                        "label": "Textfield 3",
                    }
                ],
            },
        )
