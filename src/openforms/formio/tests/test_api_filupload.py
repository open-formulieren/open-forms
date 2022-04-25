from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils.translation import gettext as _

from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.submissions.attachments import temporary_upload_from_url
from openforms.submissions.constants import UPLOADS_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin


@temp_private_root()
class FormIOTemporaryFileUploadTest(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def tearDown(self):
        self._clear_session()

    def test_upload_view_requires_active_submission(self):
        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"my content", content_type="text/bar")

        response = self.client.post(url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # add it
        self._add_submission_to_session(self.submission)

        file.seek(0)
        response = self.client.post(url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_view(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"my content", content_type="text/bar")

        response = self.client.post(url, {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body["name"], "my-file.txt")
        self.assertEqual(body["size"], 10)
        self.assertEqual(body["url"][:4], "http")

        # check if we can retrieve the file from returned url
        response = self.client.get(body["url"])
        self.assertEqual(b"".join(response.streaming_content), b"my content")
        self.assertIn("Content-Disposition", response)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("my-file.txt", response["Content-Disposition"])

        # use the convenient helper to check the model instance
        upload = temporary_upload_from_url(body["url"])
        self.assertEqual(upload.file_name, "my-file.txt")
        self.assertEqual(upload.content_type, "text/bar")
        self.assertEqual(upload.content.read(), b"my content")
        self.assertEqual(upload.file_size, 10)

        # added to session
        self.assertEqual([str(upload.uuid)], self.client.session[UPLOADS_SESSION_KEY])

    def test_upload_empty(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"", content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

        # NOTE formio displays the whole response text as message
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.data, _("The submitted file is empty."))

    @override_settings(MAX_FILE_UPLOAD_SIZE=10)  # only allow 10 bytes upload size
    def test_upload_too_large(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"a" * 11, content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 413)

    @override_settings(MAX_FILE_UPLOAD_SIZE=10)  # only allow 10 bytes upload size
    def test_spoof_upload_size_dos_vector(self):
        """
        Test that spoofing the upload size does not lead to denial-of-service attack
        vectors.

        Django itself limits the request body stream in WSGIRequest initialization
        based on the CONTENT_LENGTH header, see
        django.core.handlers.wsgi.WSGIRequest.__init__
        """
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"a" * 11, content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file},
            format="multipart",
            CONTENT_LENGTH="5",
        )

        # the limited stream causes no file to be present (can't be properly parsed)
        self.assertTrue(400 <= response.status_code < 500)
