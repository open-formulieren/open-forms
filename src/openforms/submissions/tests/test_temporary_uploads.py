import os
import uuid
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

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

        # added to session
        self.assertEqual([upload.uuid], self.client.session[UPLOADS_SESSION_KEY])

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
