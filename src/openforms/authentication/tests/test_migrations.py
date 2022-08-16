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
            auth_plugin="eherkenning",
            auth_attributes_hashed=False,
        )
        self.submission_id = submission.id

    def test_migrate_auth_data_values_not_hashed(self):
        AuthInfo = self.apps.get_model("of_authentication", "AuthInfo")

        auth_info = AuthInfo.objects.get(submission__id=self.submission_id)

        self.assertEqual(auth_info.attribute, AuthAttribute.kvk)
        self.assertEqual(auth_info.value, "123456789")
        self.assertEqual(auth_info.plugin, "eherkenning")
        self.assertFalse(auth_info.attribute_hashed)


class MigrateAuthInfoDataHashedForwardTest(TestMigrations):
    migrate_from = "0001_initial"
    migrate_to = "0002_migrate_submission_data"
    app = "of_authentication"

    def setUpBeforeMigration(self, apps):
        Submission = apps.get_model("submissions", "Submission")
        Form = apps.get_model("forms", "Form")

        form = Form.objects.create(name="Form", slug="form")
        submission = Submission.objects.create(
            form=form,
            kvk="pbkdf2_sha256$260000$fmJxoAUDp7rW735e34sKFa$EexnJj78/3x/zINzvqNbNakjC3bXYinE6mG0m0Ac5kA=",
            bsn="pbkdf2_sha256$260000$XMkgjuokLsk6ZKAXge6Qc2$imPSfmDrDw+aLjSzuTcdV6gqvuwhNwpSnXPntQo8Rrs=",
            pseudo="pbkdf2_sha256$260000$mRp5S05Og94Kohz0hx9IZD$q2ReWQ/Lzscg0qHiDKdVUWWUuuc0HdKo6Y7d1c/Tc04=",
            auth_plugin="eherkenning",
            auth_attributes_hashed=True,
        )
        self.submission_id = submission.id

    def test_migrate_auth_data_values_hashed(self):
        AuthInfo = self.apps.get_model("of_authentication", "AuthInfo")

        auth_info = AuthInfo.objects.get(submission__id=self.submission_id)

        self.assertEqual(auth_info.attribute, AuthAttribute.kvk)
        self.assertEqual(
            auth_info.value,
            "pbkdf2_sha256$260000$fmJxoAUDp7rW735e34sKFa$EexnJj78/3x/zINzvqNbNakjC3bXYinE6mG0m0Ac5kA=",
        )
        self.assertEqual(auth_info.plugin, "eherkenning")
        self.assertTrue(auth_info.attribute_hashed)
