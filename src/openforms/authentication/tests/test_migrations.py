from openforms.utils.tests.test_migrations import TestMigrations

from ..constants import AuthAttribute


class MigrateAuthInfoDataForwardTest(TestMigrations):
    migrate_from = "0001_initial"
    migrate_to = "0002_migrate_submission_data"
    app = "of_authentication"

    def setUpBeforeMigration(self, apps):
        Submission = apps.get_model("submissions", "Submission")
        Form = apps.get_model("forms", "Form")

        form = Form.objects.create(name="Form", slug="form")
        submission = Submission.objects.create(
            form=form,
            kvk="123456789",
            bsn="",
            pseudo="",
            auth_plugin="test-kvk-plugin",
            auth_attributes_hashed=True,
        )
        self.submission_id = submission.id

    def test_migrate_auth_data(self):
        AuthInfo = self.apps.get_model("of_authentication", "AuthInfo")

        auth_info = AuthInfo.objects.get(submission__id=self.submission_id)

        self.assertEqual(auth_info.attribute, AuthAttribute.kvk)
        self.assertEqual(auth_info.value, "123456789")
        self.assertEqual(auth_info.plugin, "test-kvk-plugin")
        self.assertTrue(auth_info.attribute_hashed)
