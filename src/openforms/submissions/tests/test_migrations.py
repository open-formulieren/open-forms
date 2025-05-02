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
