import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, tag
from django.utils.translation import gettext as _

import clamd
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APITransactionTestCase

from openforms.config.models import GlobalConfiguration
from openforms.submissions.attachments import temporary_upload_from_url
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

TEST_FILES = Path(__file__).parent.resolve() / "files"


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class FormIOTemporaryFileUploadTest(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()
        cls.submission_url = reverse(
            "api:submission-detail", kwargs={"uuid": cls.submission.uuid}
        )

    def tearDown(self):
        self._clear_session()

    def test_upload_view_requires_active_submission(self):
        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile(
            "my-file.txt", b"my content", content_type="text/plain"
        )

        response = self.client.post(
            url, {"file": file, "submission": self.submission_url}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # add it
        self._add_submission_to_session(self.submission)

        file.seek(0)
        response = self.client.post(
            url, {"file": file, "submission": self.submission_url}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_view(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile(
            "my-file.txt", b"my content", content_type="text/plain"
        )

        response = self.client.post(
            url, {"file": file, "submission": self.submission_url}, format="multipart"
        )
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
        assert upload is not None
        self.assertEqual(upload.file_name, "my-file.txt")
        self.assertEqual(upload.content_type, "text/plain")
        self.assertEqual(upload.content.read(), b"my content")
        self.assertEqual(upload.file_size, 10)
        self.assertEqual(upload.submission, self.submission)

    def test_soft_hyphen_upload(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile(
            "Scherm­afbeelding 2025-07-08 om 09.39.36.txt",  # note the invisible soft-hyphen here
            b"my content",
            content_type="text/plain",
        )

        response = self.client.post(
            url, {"file": file, "submission": self.submission_url}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()

        # no soft-hyphen here
        self.assertEqual(body["name"], "Schermafbeelding 2025-07-08 om 09.39.36.txt")

        response = self.client.get(body["url"])

        self.assertIn(
            "Schermafbeelding 2025-07-08 om 09.39.36.txt",  # no soft-hyphen
            response["Content-Disposition"],
        )

        # use the convenient helper to check the model instance
        upload = temporary_upload_from_url(body["url"])

        assert upload is not None

        self.assertEqual(
            upload.file_name,
            "Schermafbeelding 2025-07-08 om 09.39.36.txt",  # no soft-hyphen
        )
        self.assertEqual(upload.content_type, "text/plain")

    def test_upload_empty(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"", content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file, "submission": self.submission_url},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

        # NOTE formio displays the whole response text as message
        self.assertEqual(
            response.content.decode("utf8"), _("The submitted file is empty.")
        )
        self.assertEqual(response.content_type, "text/plain")

    @tag("security-30")
    def test_owns_submission(self):
        self._add_submission_to_session(self.submission)
        unrelated_submission = SubmissionFactory.create()

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"", content_type="text/plain")

        response = self.client.post(
            url,
            {
                "file": file,
                "submission": reverse(
                    "api:submission-detail", kwargs={"uuid": unrelated_submission.uuid}
                ),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

    def test_content_inconsistent_with_mime_type(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("pixel.png", b"GIF89a", content_type="image/png")
        response = self.client.post(url, {"file": file}, format="multipart")

        self.assertContains(
            response,
            _("The provided file is not a {file_type}.").format(
                **{"file_type": ".png"}
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @tag("gh-5507")
    def test_msg_mimetype_override(self):
        self._add_submission_to_session(self.submission)
        url = reverse("api:formio:temporary-file-upload")
        with open(Path(TEST_FILES, "sample.msg"), "rb") as f:
            file = SimpleUploadedFile(
                "sample.msg", f.read(), content_type="application/octet-stream"
            )

        response = self.client.post(
            url, {"file": file, "submission": self.submission_url}, format="multipart"
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_data = response.json()
        upload = temporary_upload_from_url(response_data["url"])
        self.assertEqual(upload.content_type, "application/vnd.ms-outlook")

    @override_settings(MAX_FILE_UPLOAD_SIZE=10)  # only allow 10 bytes upload size
    def test_upload_too_large(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"a" * 11, content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file, "submission": self.submission_url},
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
            {"file": file, "submission": self.submission_url},
            format="multipart",
            CONTENT_LENGTH="5",
        )

        # the limited stream causes no file to be present (can't be properly parsed)
        self.assertTrue(400 <= response.status_code < 500)

    @tag("gh-2520")
    def test_doc_files_can_be_uploaded(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")

        with open(Path(TEST_FILES, "test.doc"), "rb") as f:
            file = SimpleUploadedFile(
                "test.doc", f.read(), content_type="application/msword"
            )

        response = self.client.post(
            url,
            {"file": file, "submission": self.submission_url},
            format="multipart",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    @patch("openforms.formio.api.validators.GlobalConfiguration.get_solo")
    def test_file_contains_virus(self, m_config):
        m_config.return_value = GlobalConfiguration(enable_virus_scan=True)

        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file_with_virus = SimpleUploadedFile(
            "my-file.bin", clamd.EICAR, content_type="application/octet-stream"
        )

        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "instream",
                return_value={"stream": ("FOUND", "Win.Test.EICAR_HDB-1")},
            ):
                response_virus = self.client.post(
                    url,
                    {"file": file_with_virus, "submission": self.submission_url},
                    format="multipart",
                )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response_virus.status_code)
        self.assertEqual(
            response_virus.data["file"][0],
            "File did not pass the virus scan. It was found to contain 'Win.Test.EICAR_HDB-1'.",
        )

        tmpdir_contents = os.listdir(tmpdir)

        self.assertEqual(0, len(tmpdir_contents))

    @patch("openforms.formio.api.validators.GlobalConfiguration.get_solo")
    def test_file_does_not_contains_virus(self, m_config):
        m_config.return_value = GlobalConfiguration(enable_virus_scan=True)

        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file_without_virus = SimpleUploadedFile(
            "my-file.bin", b"I am a nice file", content_type="application/octet-stream"
        )

        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            with patch(
                "openforms.submissions.models.submission_files.fmt_upload_to",
                return_value="my-file.bin",
            ):
                with patch.object(
                    clamd.ClamdNetworkSocket,
                    "instream",
                    return_value={"stream": ("OK", None)},
                ):
                    response_no_virus = self.client.post(
                        url,
                        {
                            "file": file_without_virus,
                            "submission": self.submission_url,
                        },
                        format="multipart",
                    )

        self.assertEqual(status.HTTP_200_OK, response_no_virus.status_code)

        tmpdir_contents = os.listdir(tmpdir)

        self.assertEqual(["my-file.bin"], tmpdir_contents)

    @patch("openforms.formio.api.validators.GlobalConfiguration.get_solo")
    def test_file_scan_returns_error(self, m_config):
        m_config.return_value = GlobalConfiguration(enable_virus_scan=True)

        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file_with_virus = SimpleUploadedFile(
            "my-file.bin", b"I am a nice file", content_type="application/octet-stream"
        )

        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "instream",
                return_value={"stream": ("ERROR", "I am an error")},
            ):
                response_virus = self.client.post(
                    url,
                    {"file": file_with_virus, "submission": self.submission_url},
                    format="multipart",
                )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response_virus.status_code)
        self.assertEqual(
            response_virus.data["file"][0],
            "The virus scan on this file returned an error.",
        )

        tmpdir_contents = os.listdir(tmpdir)

        self.assertEqual(0, len(tmpdir_contents))

    @patch("openforms.formio.api.validators.GlobalConfiguration.get_solo")
    def test_file_scan_returns_unexpected_status(self, m_config):
        m_config.return_value = GlobalConfiguration(enable_virus_scan=True)

        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file_with_virus = SimpleUploadedFile(
            "my-file.bin", b"I am a nice file", content_type="application/octet-stream"
        )

        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "instream",
                return_value={"stream": ("UNEXPECTED", "I am message")},
            ):
                response_virus = self.client.post(
                    url,
                    {"file": file_with_virus, "submission": self.submission_url},
                    format="multipart",
                )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response_virus.status_code)
        self.assertEqual(
            response_virus.data["file"][0],
            "The virus scan returned an unexpected status.",
        )

        tmpdir_contents = os.listdir(tmpdir)

        self.assertEqual(0, len(tmpdir_contents))

    @patch("openforms.formio.api.validators.GlobalConfiguration.get_solo")
    def test_cannot_connect_to_clamdav(self, m_config):
        m_config.return_value = GlobalConfiguration(enable_virus_scan=True)

        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")
        file_with_virus = SimpleUploadedFile(
            "my-file.bin", b"I am a nice file", content_type="application/octet-stream"
        )

        tmpdir = tempfile.mkdtemp()
        with override_settings(PRIVATE_MEDIA_ROOT=tmpdir, SENDFILE_ROOT=tmpdir):
            with patch.object(
                clamd.ClamdNetworkSocket,
                "instream",
                side_effect=clamd.ConnectionError("Cannot connect!"),
            ):
                response_virus = self.client.post(
                    url,
                    {"file": file_with_virus, "submission": self.submission_url},
                    format="multipart",
                )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response_virus.status_code)
        self.assertEqual(
            response_virus.data["file"][0],
            "The virus scan could not be performed at this time. Please retry later.",
        )

        tmpdir_contents = os.listdir(tmpdir)

        self.assertEqual(0, len(tmpdir_contents))

    def test_filename_with_spaces(self):
        self._add_submission_to_session(self.submission)

        url = reverse("api:formio:temporary-file-upload")

        with self.subTest("File with leading spaces"):
            file = SimpleUploadedFile(
                "   my-file.txt", b"my content", content_type="text/plain"
            )
            response = self.client.post(
                url,
                {"file": file, "submission": self.submission_url},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            body = response.json()
            self.assertEqual(body["name"], "   my-file.txt")

            # check if we can retrieve the file from returned url
            response = self.client.get(body["url"])
            self.assertIn("my-file.txt", response["Content-Disposition"])

            # use the convenient helper to check the model instance
            upload = temporary_upload_from_url(body["url"])
            assert upload is not None
            self.assertEqual(upload.file_name, "   my-file.txt")

        with self.subTest("File with trailing spaces"):
            file = SimpleUploadedFile(
                "my-file   .txt", b"my content", content_type="text/plain"
            )
            response = self.client.post(
                url,
                {"file": file, "submission": self.submission_url},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            body = response.json()
            self.assertEqual(body["name"], "my-file   .txt")

            # check if we can retrieve the file from returned url
            response = self.client.get(body["url"])
            self.assertIn("my-file   .txt", response["Content-Disposition"])

            # use the convenient helper to check the model instance
            upload = temporary_upload_from_url(body["url"])
            assert upload is not None
            self.assertEqual(upload.file_name, "my-file   .txt")


@override_settings(
    # Deliberately set to cache backend to not fall in the trap of using DB row-level
    # locking. This also reflects how we deploy in prod.
    SESSION_ENGINE="django.contrib.sessions.backends.cache",
    SESSION_CACHE_ALIAS="session",
    CACHES={
        **settings.CACHES,
        "session": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    },
)
class ConcurrentUploadTests(SubmissionsMixin, APITransactionTestCase):
    @tag("gh-3858")
    def test_concurrent_file_uploads(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "file",
                    "label": "Some upload",
                    "multiple": True,
                }
            ]
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:formio:temporary-file-upload")

        def do_upload() -> str:
            file = SimpleUploadedFile(
                "my-file.txt", b"my content", content_type="text/plain"
            )
            response = self.client.post(
                endpoint,
                {
                    "file": file,
                    "submission": reverse(
                        "api:submission-detail", kwargs={"uuid": submission.uuid}
                    ),
                },
                format="multipart",
            )
            assert response.status_code == status.HTTP_200_OK
            resp_data = response.json()
            return resp_data["url"]

        # do both uploads in parallel in their own thread
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(do_upload) for _ in range(0, 2)]
            urls = [future.result() for future in as_completed(futures)]

        # check that we can access the detail endpoint for each upload
        for detail_url in urls:
            with self.subTest(url=detail_url):
                response = self.client.get(detail_url)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
