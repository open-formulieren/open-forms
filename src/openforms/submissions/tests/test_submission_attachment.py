import os
from pathlib import Path
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings, tag
from django.urls import reverse

from PIL import Image, UnidentifiedImageError
from privates.test import temp_private_root
from rest_framework.exceptions import ValidationError

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.api.exceptions import RequestEntityTooLarge
from openforms.forms.tests.factories import FormStepFactory
from openforms.tests.utils import disable_2fa

from ..attachments import (
    append_file_num_postfix,
    attach_uploads_to_submission_step,
    clean_mime_type,
    cleanup_submission_temporary_uploaded_files,
    resize_attachment,
    resolve_uploads_from_data,
)
from ..models import SubmissionFileAttachment
from .factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionStepFactory,
    TemporaryFileUploadFactory,
)
from .mixins import VariablesTestMixin

TEST_FILES_DIR = Path(__file__).parent / "files"


@temp_private_root()
class SubmissionAttachmentTest(VariablesTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.test_image_path = (TEST_FILES_DIR / "image-256x256.png").resolve()

    def test_resolve_uploads_from_formio_data(self):
        upload = TemporaryFileUploadFactory.create()
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                        "form": "",
                        "name": "my-image.jpg",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                    "size": 46114,
                    "type": "image/jpg",
                    "storage": "url",
                    "originalName": "my-image.jpg",
                }
            ],
        }
        components = [
            {"key": "my_normal_key", "type": "text"},
            {"key": "my_file", "type": "file"},
        ]
        actual = resolve_uploads_from_data(components, data)
        self.assertEqual(actual, {"my_file": (components[1], [upload])})

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_uploads_to_submission_step(self, resize_mock):
        upload = TemporaryFileUploadFactory.create(file_name="my-image.jpg")
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                        "form": "",
                        "name": "my-image.jpg",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                    "size": 46114,
                    "type": "image/jpg",
                    "storage": "url",
                    "originalName": "my-image.jpg",
                }
            ],
        }
        components = [
            {"key": "my_normal_key", "type": "text"},
            {"key": "my_file", "type": "file", "file": {"name": "my-filename.txt"}},
        ]
        form_step = FormStepFactory.create(
            form_definition__configuration={"components": components}
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission__form=form_step.form, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], True)  # created new
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

        attachment = submission_step.attachments.get()
        self.assertEqual(attachment.form_key, "my_file")
        self.assertEqual(attachment.file_name, "my-filename.jpg")
        self.assertEqual(attachment.original_name, "my-image.jpg")
        self.assertEqual(attachment.content.read(), b"content")
        self.assertEqual(attachment.content_type, upload.content_type)
        self.assertEqual(attachment.temporary_file, upload)

        # test attaching again is idempotent
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], False)  # not created
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

        # test cleanup
        cleanup_submission_temporary_uploaded_files(submission_step.submission)
        attachment.refresh_from_db()
        self.assertEqual(attachment.temporary_file, None)
        # verify the new FileField has its own content
        self.assertEqual(attachment.content.read(), b"content")

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_multiple_uploads_to_submission_step(self, resize_mock):
        upload_1 = TemporaryFileUploadFactory.create(file_name="my-image-1.jpg")
        upload_2 = TemporaryFileUploadFactory.create(file_name="my-image-2.jpg")
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload_1.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload_1.uuid}",
                        "form": "",
                        "name": "my-image-1.jpg",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                    "size": 46114,
                    "type": "image/jpg",
                    "storage": "url",
                    "originalName": "my-image-1.jpg",
                },
                {
                    "url": f"http://server/api/v1/submissions/files/{upload_2.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload_2.uuid}",
                        "form": "",
                        "name": "my-image-2.jpg",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-22305610-2da4-4694-a341-ccb919c3d544.jpg",
                    "size": 46114,
                    "type": "image/jpg",
                    "storage": "url",
                    "originalName": "my-image-2.jpg",
                },
            ],
        }
        components = [
            {"key": "my_normal_key", "type": "text"},
            {
                "key": "my_file",
                "type": "file",
                "multiple": True,
                "file": {"name": "my-filename.txt"},
            },
        ]
        form_step = FormStepFactory.create(
            form_definition__configuration={"components": components}
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission__form=form_step.form, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], True)  # created new
        self.assertEqual(result[1][1], True)  # created new
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

        attachments = list(submission_step.attachments.all())

        # expect the names to have postfixes
        attachment_1 = attachments[0]
        attachment_2 = attachments[1]

        self.assertSetEqual(
            {attachment_1.file_name, attachment_2.file_name},
            {"my-filename-1.jpg", "my-filename-2.jpg"},
        )
        self.assertSetEqual(
            {attachment_1.original_name, attachment_2.original_name},
            {"my-image-1.jpg", "my-image-2.jpg"},
        )

        # test attaching again is idempotent
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], False)  # not created
        self.assertEqual(result[1][1], False)  # not created
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_attach_uploads_to_submission_step_resizes_image(self):
        upload = TemporaryFileUploadFactory.create(
            file_name="my-image.png", content=File(open(self.test_image_path, "rb"))
        )
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                        "form": "",
                        "name": "my-image.png",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 46114,
                    "type": "image/png",
                    "storage": "url",
                    "originalName": "my-image.png",
                }
            ],
        }
        components = [
            {"key": "my_normal_key", "type": "text"},
            {
                "key": "my_file",
                "type": "file",
                "of": {
                    "image": {"resize": {"apply": True, "width": 100, "height": 100}}
                },
            },
        ]
        form_step = FormStepFactory.create(
            form_definition__configuration={"components": components}
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission__form=form_step.form, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], True)  # created new
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

        # verify resize
        attachment = submission_step.attachments.get()
        self.assertEqual(attachment.form_key, "my_file")
        self.assertEqual(attachment.original_name, "my-image.png")
        self.assertImageSize(attachment.content, 100, 100, "png")

    def test_attach_upload_larger_than_configured_max_size_raises_413(self):
        """
        Continuing with too-large fields must raise a HTTP 413.

        Formio validates client-side that the files are not too big. Thus, anyone
        continuing with uploads that are too large for the field are most likely using
        Postman/curl/... We are protecting against client-side validation bypasses here
        by validating the upload sizes when the temporary uploads are connect to the
        respective Formio component.
        """
        components = [
            {
                "key": "my_file",
                "type": "file",
                "fileMaxSize": "10B",
            },
        ]
        upload = TemporaryFileUploadFactory.create(
            file_name="aaa.txt", content__data=b"a" * 20, file_size=20
        )
        data = {
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload.uuid}",
                        "form": "",
                        "name": "aaa.txt",
                        "size": 20,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "aaa-12305610-2da4-4694-a341-ccb919c3d543.txt",
                    "size": 20,
                    "type": "text/plain",
                    "storage": "url",
                    "originalName": "aaa.txt",
                }
            ],
        }
        submission = SubmissionFactory.from_components(
            completed=False,
            with_report=False,
            components_list=components,
            submitted_data=data,
        )
        submission_step = submission.submissionstep_set.get()

        with self.assertRaises(RequestEntityTooLarge):
            attach_uploads_to_submission_step(submission_step)

    @tag("GHSA-h85r-xv4w-cg8g")
    def test_attach_upload_validates_file_content_types_malicious_content(self):
        """
        Regression test for CVE-2022-31041 to ensure the file content is validated
        against the formio configuration.

        We cannot rely on file extension or browser mime-type. Therefore, we have a test
        file that claims to be a PDF but is actually an image that we put in the upload
        data. The step attaching the uploads to the form data must validate the
        configuration.
        """
        with open(TEST_FILES_DIR / "image-256x256.pdf", "rb") as infile:
            upload1 = TemporaryFileUploadFactory.create(
                file_name="my-pdf.pdf",
                content=File(infile),
                content_type="application/pdf",
            )
            upload2 = TemporaryFileUploadFactory.create(
                file_name="my-pdf2.pdf", content=File(infile), content_type="image/png"
            )

        data = {
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload1.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload1.uuid}",
                        "form": "",
                        "name": "my-pdf.pdf",
                        "size": 585,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-pdf-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 585,
                    "type": "application/pdf",  # we are lying!
                    "storage": "url",
                    "originalName": "my-pdf.pdf",
                },
                {
                    "url": f"http://server/api/v1/submissions/files/{upload2.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload2.uuid}",
                        "form": "",
                        "name": "my-pdf2.pdf",
                        "size": 585,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-pdf2-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 585,
                    "type": "image/png",  # we are lying!
                    "storage": "url",
                    "originalName": "my-pdf2.pdf",
                },
            ],
        }
        formio_components = {
            "key": "my_file",
            "type": "file",
            "multiple": True,
            "file": {
                "name": "",
                "type": ["application/pdf"],
            },
            "filePattern": "application/pdf",
        }

        submission = SubmissionFactory.from_components(
            [formio_components],
            submitted_data=data,
        )
        submission_step = submission.submissionstep_set.get()

        with self.assertRaises(ValidationError) as err_context:
            attach_uploads_to_submission_step(submission_step)

        validation_error = err_context.exception.get_full_details()
        self.assertEqual(len(validation_error["my_file"]), 2)

    @tag("GHSA-h85r-xv4w-cg8g")
    def test_attach_upload_validates_file_content_types_ok(self):
        """
        Regression test for CVE-2022-31041 to ensure the file content is validated
        against the formio configuration.

        We cannot rely on file extension or browser mime-type. Therefore, we have a test
        file that claims to be a PDF but is actually an image that we put in the upload
        data. The step attaching the uploads to the form data must validate the
        configuration.
        """
        with open(TEST_FILES_DIR / "image-256x256.png", "rb") as infile:
            upload1 = TemporaryFileUploadFactory.create(
                file_name="my-img.png",
                content=File(infile),
                content_type="image/png",
            )
            upload2 = TemporaryFileUploadFactory.create(
                file_name="my-img2.png", content=File(infile), content_type="image/png"
            )

        data = {
            "my_file": [
                {
                    "url": f"http://server/api/v1/submissions/files/{upload1.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload1.uuid}",
                        "form": "",
                        "name": "my-img.png",
                        "size": 585,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-img-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 585,
                    "type": "image/png",  # we are lying!
                    "storage": "url",
                    "originalName": "my-img.png",
                },
                {
                    "url": f"http://server/api/v1/submissions/files/{upload2.uuid}",
                    "data": {
                        "url": f"http://server/api/v1/submissions/files/{upload2.uuid}",
                        "form": "",
                        "name": "my-img2.png",
                        "size": 585,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-img2-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 585,
                    "type": "image/png",  # we are lying!
                    "storage": "url",
                    "originalName": "my-img2.png",
                },
            ],
        }
        formio_components = {
            "key": "my_file",
            "type": "file",
            "multiple": True,
            "file": {
                "name": "",
                "type": ["image/png", "image/jpeg"],
            },
            "filePattern": "image/png,image/jpeg",
        }

        submission = SubmissionFactory.from_components(
            [formio_components],
            submitted_data=data,
        )
        submission_step = submission.submissionstep_set.get()

        try:
            attach_uploads_to_submission_step(submission_step)
        except ValidationError:
            self.fail("Uploads should be accepted since the content types are valid")

    @disable_2fa
    def test_attachment_retrieve_view_requires_permission(self):
        attachment = SubmissionFileAttachmentFactory.create()
        url = reverse(
            "admin:submissions_submissionfileattachment_content",
            kwargs={"pk": attachment.id},
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        user = SuperUserFactory()
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def assertImageSize(self, file, width, height, format):
        image = Image.open(file, formats=(format,))
        self.assertEqual(image.width, width)
        self.assertEqual(image.height, height)

    def test_assertImageSize(self):
        self.assertImageSize(self.test_image_path, 256, 256, "png")

        with self.assertRaises(AssertionError):
            self.assertImageSize(self.test_image_path, 1000, 256, "png")
        with self.assertRaises(AssertionError):
            self.assertImageSize(self.test_image_path, 256, 1000, "png")
        with self.assertRaises(UnidentifiedImageError):
            self.assertImageSize(self.test_image_path, 256, 256, "jpeg")

    def test_resize_attachment_helper(self):
        with open(self.test_image_path, "rb") as f:
            data = f.read()

        attachment = SubmissionFileAttachmentFactory.create(
            content__name="my-image.png", content__data=data
        )
        # too small to resize
        res = resize_attachment(attachment, (1024, 1024))
        self.assertEqual(res, False)

        # same size as required
        res = resize_attachment(attachment, (256, 256))
        self.assertEqual(res, False)

        # good, actually resize
        res = resize_attachment(attachment, (200, 200))
        self.assertEqual(res, True)
        self.assertImageSize(attachment.content, 200, 200, "png")

        # but not resize again to same size
        res = resize_attachment(attachment, (200, 200))
        self.assertEqual(res, False)

        # don't crash on corrupt image
        attachment_bad = SubmissionFileAttachmentFactory.create(
            content__name="my-image.png", content__data=b"broken"
        )
        res = resize_attachment(attachment_bad, (1024, 1024))
        self.assertEqual(res, False)

        # don't crash on missing file
        attachment_bad = SubmissionFileAttachmentFactory.create()
        attachment_bad.content.delete()
        res = resize_attachment(attachment_bad, (1024, 1024))
        self.assertEqual(res, False)

    def test_append_file_num_postfix_helper(self):
        actual = append_file_num_postfix("orginal.txt", "new.bin", 1, 1)
        self.assertEqual("new.txt", actual)

        actual = append_file_num_postfix("orginal.txt", "new.bin", 1, 5)
        self.assertEqual("new-1.txt", actual)

        actual = append_file_num_postfix("orginal.txt", "new.bin", 2, 5)
        self.assertEqual("new-2.txt", actual)

        actual = append_file_num_postfix("orginal.txt", "new.bin", 1, 20)
        self.assertEqual("new-01.txt", actual)

        actual = append_file_num_postfix("orginal.txt", "new.bin", 11, 20)
        self.assertEqual("new-11.txt", actual)

    def test_clean_mime_type_helper(self):
        actual = clean_mime_type("text/plain")
        self.assertEqual("text/plain", actual)

        actual = clean_mime_type("text/plain/xxx")
        self.assertEqual("text/plain", actual)

        actual = clean_mime_type("text/plain-xxx")
        self.assertEqual("text/plain-xxx", actual)

        actual = clean_mime_type("text/plain-x.x.x")
        self.assertEqual("text/plain-x.x.x", actual)

        actual = clean_mime_type("xxxx")
        self.assertEqual("application/octet-stream", actual)

        actual = clean_mime_type("")
        self.assertEqual("application/octet-stream", actual)

    def test_content_hash_calculation(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            content__data=b"a predictable hash source"
        )
        # generated using https://passwordsgenerator.net/sha256-hash-generator/
        expected_content_hash = (
            "21bfcc609236ad74408c0e9c73e2e9ef963f676e36c4586f18d75e65c3b0e0df"
        )

        self.assertEqual(submission_file_attachment.content_hash, expected_content_hash)
