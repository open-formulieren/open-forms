from django.test import TestCase, override_settings
from django.urls import reverse

from furl import furl
from privates.test import temp_private_root

from .factories import SubmissionFileAttachmentFactory


@override_settings(SENDFILE_BACKEND="django_sendfile.backends.nginx")
@temp_private_root()
class SubmissionAttachmentDownloadTest(TestCase):
    def test_incomplete_submission_404(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=False,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": "dummy-hash"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_submission_not_registered_yet_404(self):
        submission_file_attachments = [
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_failed=True,
            ),
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_pending=True,
            ),
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_in_progress=True,
            ),
        ]

        for submission_file_attachment in submission_file_attachments:
            with self.subTest(submission_file_attachment):
                path = reverse(
                    "submissions:attachment-download",
                    kwargs={"uuid": submission_file_attachment.uuid},
                )
                url = furl(path).add({"hash": "dummy-hash"})

                response = self.client.get(url)

                self.assertEqual(response.status_code, 404)

    def test_valid_preconditions_missing_hash_403(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )

        response = self.client.get(path)

        self.assertEqual(response.status_code, 403)

    def test_valid_preconditions_invalid_hash_403(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": "badhash"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
