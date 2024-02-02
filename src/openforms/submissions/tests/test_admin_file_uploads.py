from django.test import override_settings, tag
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from privates.test import temp_private_root

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import SubmissionFileAttachmentFactory, TemporaryFileUploadFactory


@disable_admin_mfa()
@temp_private_root()
class TemporaryFileUploadsAdmin(WebTest):
    @tag("CVE-2022-36359")
    @override_settings(SENDFILE_BACKEND="django_sendfile.backends.nginx")
    def test_filenames_properly_escaped(self):
        """
        Equivalent test for Django's CVE-2022-36359.

        Ensure that filenames are correctly escaped so they don't lead to reflected
        file downloads when staff users download the attachments of end-users.

        Tests taken from Django:
        https://github.com/django/django/commit/bd062445cffd3f6cc6dcd20d13e2abed818fa173
        """
        user = SuperUserFactory.create()
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
                url = reverse(
                    "admin:submissions_temporaryfileupload_change", args=(upload.pk,)
                )

                detail_page = self.app.get(url, user=user)
                self.assertEqual(detail_page.status_code, 200)
                # this doesn't work, as there is a bug with read-only fields that don't get the proper URL
                # download_response = detail_page.click(description=upload.content.name)

                download_url = reverse(
                    "admin:submissions_temporaryfileupload_content", args=(upload.pk,)
                )
                download_response = self.app.get(download_url)

                self.assertEqual(
                    download_response.headers["Content-Disposition"],
                    f'attachment; filename="{escaped}"',
                )


@disable_admin_mfa()
@temp_private_root()
class SubmissionAttachmensAdmin(WebTest):
    @tag("CVE-2022-36359")
    @override_settings(SENDFILE_BACKEND="django_sendfile.backends.nginx")
    def test_filenames_properly_escaped(self):
        """
        Equivalent test for Django's CVE-2022-36359.

        Ensure that filenames are correctly escaped so they don't lead to reflected
        file downloads when staff users download the attachments of end-users.

        Tests taken from Django:
        https://github.com/django/django/commit/bd062445cffd3f6cc6dcd20d13e2abed818fa173
        """
        user = SuperUserFactory.create()
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
                attachment = SubmissionFileAttachmentFactory.create(
                    file_name="", original_name=filename
                )

                download_url = reverse(
                    "admin:submissions_submissionfileattachment_content",
                    args=(attachment.pk,),
                )
                download_response = self.app.get(download_url, user=user)

                self.assertEqual(
                    download_response.headers["Content-Disposition"],
                    f'attachment; filename="{escaped}"',
                )
