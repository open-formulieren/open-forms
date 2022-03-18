import os
import uuid
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, override_settings
from django.utils.translation import gettext as _

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.submissions.attachments import (
    cleanup_unclaimed_temporary_uploaded_files,
    temporary_upload_from_url,
    temporary_upload_uuid_from_url,
)
from openforms.submissions.constants import UPLOADS_SESSION_KEY
from openforms.submissions.models import TemporaryFileUpload
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    TemporaryFileUploadFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.submissions.utils import (
    add_upload_to_session,
    append_to_session_list,
    remove_from_session_list,
    remove_upload_from_session,
)
from openforms.tests.utils import disable_2fa


@temp_private_root()
class TemporaryFileUploadTest(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.create()

    def tearDown(self):
        self._clear_session()

    def test_temporary_upload_uuid_from_url(self):
        request = RequestFactory().get("/")
        identifier = str(uuid.uuid4())
        url = reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": identifier},
            request=request,
        )

        # good
        actual = temporary_upload_uuid_from_url(url)
        self.assertEqual(actual, identifier)

        # bad
        self.assertIsNone(temporary_upload_uuid_from_url("http://xxx/yyy"))
        self.assertIsNone(temporary_upload_uuid_from_url("/yyy"))

    def test_temporary_upload_from_url(self):
        request = RequestFactory().get("/")
        upload = TemporaryFileUploadFactory.create()
        url = reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": upload.uuid},
            request=request,
        )

        # good
        actual = temporary_upload_from_url(url)
        self.assertEqual(actual, upload)

        # bad
        self.assertIsNone(temporary_upload_from_url("http://xxx/yyy"))
        self.assertIsNone(temporary_upload_from_url("/yyy"))

    def test_upload_view_requires_active_submission(self):
        url = reverse("api:submissions:temporary-file-upload")
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

        url = reverse("api:submissions:temporary-file-upload")
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

        url = reverse("api:submissions:temporary-file-upload")
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

        url = reverse("api:submissions:temporary-file-upload")
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

        url = reverse("api:submissions:temporary-file-upload")
        file = SimpleUploadedFile("my-file.txt", b"a" * 11, content_type="text/plain")

        response = self.client.post(
            url,
            {"file": file},
            format="multipart",
            CONTENT_LENGTH="5",
        )

        # the limited stream causes no file to be present (can't be properly parsed)
        self.assertTrue(400 <= response.status_code < 500)

    def test_delete_view_requires_registered_uploads(self):
        upload = TemporaryFileUploadFactory.create()
        url = reverse("api:submissions:temporary-file", kwargs={"uuid": upload.uuid})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # add it
        self._add_upload_to_session(upload)

        d = dict(self.client.session)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_view(self):
        upload = TemporaryFileUploadFactory.create()
        path = upload.content.path
        self.assertTrue(os.path.exists(path))

        self._add_upload_to_session(upload)

        url = reverse("api:submissions:temporary-file", kwargs={"uuid": upload.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # expect the file and instance to be deleted
        self.assertFalse(os.path.exists(path))

        with self.assertRaisesRegex(FileNotFoundError, r"No such file or directory:"):
            upload.content.read()

        with self.assertRaises(TemporaryFileUpload.DoesNotExist):
            upload.refresh_from_db()

        # 403 (because permission check fails before object is retrieved)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # gone
        self.assertEqual([], self.client.session[UPLOADS_SESSION_KEY])

    def test_delete_instance_method(self):
        upload = TemporaryFileUploadFactory.create()
        path = upload.content.path
        self.assertTrue(os.path.exists(path))

        with capture_on_commit_callbacks(execute=True):
            upload.delete()

        # expect the file and instance to be deleted
        self.assertFalse(os.path.exists(path))

        with self.assertRaisesMessage(
            ValueError, "The 'content' attribute has no file associated with it."
        ):
            upload.content.read()

        with self.assertRaises(TemporaryFileUpload.DoesNotExist):
            upload.refresh_from_db()

    def test_delete_queryset_method(self):
        uploads = TemporaryFileUploadFactory.create_batch(3)
        paths = [u.content.path for u in uploads]
        for path in paths:
            self.assertTrue(os.path.exists(path))

        with capture_on_commit_callbacks(execute=True):
            TemporaryFileUpload.objects.all().delete()

        for path in paths:
            self.assertFalse(os.path.exists(path))

    def test_cleanup_unclaimed_temporary_uploaded_files(self):
        with freeze_time("2020-06-01 10:00"):
            remove_1 = TemporaryFileUploadFactory.create()

        with freeze_time("2020-06-02 10:00"):
            remove_2 = TemporaryFileUploadFactory.create()
            keep_1 = TemporaryFileUploadFactory.create()
            SubmissionFileAttachmentFactory.create(temporary_file=keep_1)

        with freeze_time("2020-06-03 10:00"):
            keep_2 = TemporaryFileUploadFactory.create()

        with freeze_time("2020-06-04 10:00"):
            keep_3 = TemporaryFileUploadFactory.create()
            cleanup_unclaimed_temporary_uploaded_files(timedelta(days=1))

        actual = list(TemporaryFileUpload.objects.all())
        # expect the unclaimed & older uploads to be deleted
        self.assertEqual(actual, [keep_1, keep_2, keep_3])

    @disable_2fa
    def test_upload_retrieve_requires_permission(self):
        upload = TemporaryFileUploadFactory.create()
        url = reverse(
            "admin:submissions_temporaryfileupload_content", kwargs={"pk": upload.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        user = SuperUserFactory()
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_session_utils(self):
        session = self.client.session

        # append values
        append_to_session_list(session, "my_key", 1)
        self.assertEqual(session["my_key"], [1])
        append_to_session_list(session, "my_key", 2)
        self.assertEqual(session["my_key"], [1, 2])

        # no duplicates
        append_to_session_list(session, "my_key", 2)
        self.assertEqual(session["my_key"], [1, 2])

        # remove value
        remove_from_session_list(session, "my_key", 2)
        self.assertEqual(session["my_key"], [1])

        # ignore values never added
        remove_from_session_list(session, "my_key", 3)

    def test_session_upload_utils(self):
        session = self.client.session

        upload_1 = TemporaryFileUploadFactory.create()
        upload_2 = TemporaryFileUploadFactory.create()
        add_upload_to_session(upload_1, session)
        add_upload_to_session(upload_2, session)

        session_uploads = session[UPLOADS_SESSION_KEY]
        self.assertEqual([str(upload_1.uuid), str(upload_2.uuid)], session_uploads)

        remove_upload_from_session(upload_1, session)
        self.assertEqual([str(upload_2.uuid)], session_uploads)
