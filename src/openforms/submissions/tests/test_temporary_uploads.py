import os
import uuid
from datetime import timedelta

from django.test import RequestFactory, tag

from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa
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
from openforms.submissions.models import TemporaryFileUpload
from openforms.submissions.models.submission_files import SubmissionFileAttachment
from openforms.submissions.tests.factories import (
    SubmissionFileAttachmentFactory,
    TemporaryFileUploadFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.submissions.utils import append_to_session_list, remove_from_session_list


@temp_private_root()
class TemporaryFileUploadTest(SubmissionsMixin, APITestCase):

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

    @tag("CVE-2022-36359")
    def test_filename_properly_escaped(self):
        """
        Equivalent test for Django's CVE-2022-36359.

        Ensure that filenames are correctly escaped so they don't lead to reflected
        file downloads when staff users download the attachments of end-users.

        Tests taken from Django:
        https://github.com/django/django/commit/bd062445cffd3f6cc6dcd20d13e2abed818fa173
        """
        tests = [
            ('multi-part-one";" dummy".txt', r"multi-part-one\";\" dummy\".txt"),
            ('multi-part-one\\";" dummy".txt', r"multi-part-one\\\";\" dummy\".txt"),
            (
                'multi-part-one\\";\\" dummy".txt',
                r"multi-part-one\\\";\\\" dummy\".txt",
            ),
        ]

        for filename, escaped in tests:
            with self.subTest(filename=filename, escaped=escaped):
                upload = TemporaryFileUploadFactory.create(file_name=filename)
                self._add_submission_to_session(upload.submission)
                url = reverse(
                    "api:submissions:temporary-file", kwargs={"uuid": upload.uuid}
                )

                response = self.client.get(url)

                self.assertEqual(
                    response.headers["Content-Disposition"],
                    f'attachment; filename="{escaped}"',
                )

    def test_delete_view_requires_registered_uploads(self):
        upload = TemporaryFileUploadFactory.create()
        url = reverse("api:submissions:temporary-file", kwargs={"uuid": upload.uuid})

        with self.subTest("upload submission not in session"):
            response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("upload submission added to session"):
            self._add_submission_to_session(upload.submission)

            response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_view(self):
        upload = TemporaryFileUploadFactory.create()
        path = upload.content.path
        self.assertTrue(os.path.exists(path))
        self._add_submission_to_session(upload.submission)

        url = reverse("api:submissions:temporary-file", kwargs={"uuid": upload.uuid})

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(
                url,
                HTTP_ACCEPT="application/json",
                content_type="application/json",
            )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # expect the file and instance to be deleted
        self.assertFalse(os.path.exists(path))

        with self.assertRaisesRegex(FileNotFoundError, r"No such file or directory:"):
            upload.content.read()

        with self.assertRaises(TemporaryFileUpload.DoesNotExist):
            upload.refresh_from_db()

        # 404 because the object cannot be found anymore
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_instance_method(self):
        upload = TemporaryFileUploadFactory.create()
        path = upload.content.path
        self.assertTrue(os.path.exists(path))

        with self.captureOnCommitCallbacks(execute=True):
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

        with self.captureOnCommitCallbacks(execute=True):
            TemporaryFileUpload.objects.all().delete()

        for path in paths:
            self.assertFalse(os.path.exists(path))

    def test_delete_temporary_file_attachement_deletes_the_saved_one_as_well(self):
        upload = TemporaryFileUploadFactory.create()
        self._add_submission_to_session(upload.submission)
        saved_upload = SubmissionFileAttachmentFactory.create(temporary_file=upload)
        url = reverse("api:submissions:temporary-file", kwargs={"uuid": upload.uuid})

        # make sure the two files exist
        self.assertEqual(TemporaryFileUpload.objects.get(), upload)
        self.assertEqual(SubmissionFileAttachment.objects.get(), saved_upload)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TemporaryFileUpload.objects.exists())
        self.assertFalse(SubmissionFileAttachment.objects.exists())

    def test_cleanup_unclaimed_temporary_uploaded_files(self):
        with freeze_time("2020-06-01 10:00"):
            TemporaryFileUploadFactory.create()

        with freeze_time("2020-06-02 10:00"):
            TemporaryFileUploadFactory.create()
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

    @disable_admin_mfa()
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
