from io import BytesIO

from django.core.files import File
from django.db.migrations.state import StateApps

from openforms.utils.tests.test_migrations import TestMigrations


class AddSubmissionToTemporaryFileUploadMigrationTests(TestMigrations):
    app = "submissions"
    migrate_from = "0004_auto_20231128_1536"
    migrate_to = "0007_add_legacy_constraint"

    def setUpBeforeMigration(self, apps: StateApps):
        TemporaryFileUpload = apps.get_model("submissions", "TemporaryFileUpload")
        TemporaryFileUpload.objects.create(
            content=File(BytesIO(b"content")),
            file_name="test",
            content_type="application/foo",
        )

    def test_legacy_true(self):
        TemporaryFileUpload = self.apps.get_model("submissions", "TemporaryFileUpload")
        instance = TemporaryFileUpload.objects.get()

        self.assertTrue(instance.legacy)
        self.assertIsNone(instance.submission)
