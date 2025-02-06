from pathlib import Path
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings, tag
from django.urls import reverse

from maykin_2fa.test import disable_admin_mfa
from PIL import Image, UnidentifiedImageError
from privates.test import temp_private_root

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.api.exceptions import RequestEntityTooLarge
from openforms.forms.tests.factories import FormStepFactory

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

TEST_FILES_DIR = Path(__file__).parent / "files"


@temp_private_root()
class SubmissionAttachmentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.test_image_path = (TEST_FILES_DIR / "image-256x256.png").resolve()

    def test_resolve_uploads_from_formio_data(self):
        upload = TemporaryFileUploadFactory.create()
        upload_in_column = TemporaryFileUploadFactory.create()
        upload_in_fieldset = TemporaryFileUploadFactory.create()

        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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
            "fileInColumn": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload_in_column.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_in_column.uuid}",
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
            "fileInFieldset": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload_in_fieldset.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_in_fieldset.uuid}",
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
            {
                "key": "columnWithFile",
                "type": "columns",
                "columns": [{"key": "fileInColumn", "type": "file"}],
            },
            {
                "type": "fieldset",
                "key": "aFieldsetWithFile",
                "components": [{"key": "fileInFieldset", "type": "file"}],
            },
        ]
        actual = resolve_uploads_from_data({"components": components}, data)
        self.assertEqual(
            actual,
            {
                "my_file": (components[1], [upload], "components.1"),
                "fileInColumn": (
                    components[2]["columns"][0],
                    [upload_in_column],
                    "components.2.columns.0",
                ),
                "fileInFieldset": (
                    components[3]["components"][0],
                    [upload_in_fieldset],
                    "components.3.components.0",
                ),
            },
        )

    def test_resolve_nested_uploads(self):
        upload_in_repeating_group_1, upload_in_repeating_group_2, nested_upload = (
            TemporaryFileUploadFactory.create_batch(3)
        )
        data = {
            "repeatingGroup": [
                {
                    "fileInRepeatingGroup": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                    ]
                },
                {
                    "fileInRepeatingGroup": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                    ]
                },
            ],
            "nested": {
                "file": [
                    {
                        "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
                        "data": {
                            "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
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
            },
        }
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [{"type": "file", "key": "fileInRepeatingGroup"}],
                },
                {"key": "nested.file", "type": "file"},
            ]
        }

        actual = resolve_uploads_from_data(
            configuration,
            data,
        )

        self.assertEqual(
            actual,
            {
                "repeatingGroup.0.fileInRepeatingGroup": (
                    configuration["components"][0]["components"][0],
                    [upload_in_repeating_group_1],
                    "components.0.components.0",
                ),
                "repeatingGroup.1.fileInRepeatingGroup": (
                    configuration["components"][0]["components"][0],
                    [upload_in_repeating_group_2],
                    "components.0.components.0",
                ),
                "nested.file": (
                    configuration["components"][1],
                    [nested_upload],
                    "components.1",
                ),
            },
        )

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_uploads_to_submission_step(self, resize_mock):
        upload = TemporaryFileUploadFactory.create(file_name="my-image.jpg")
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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
            form=upload.submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=upload.submission, data=data
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
        self.assertIsNotNone(attachment.submission_variable)
        self.assertEqual(attachment.submission_variable.key, "my_file")

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
    def test_attach_files_in_fieldset(self, resize_mock):
        upload = TemporaryFileUploadFactory.create(file_name="test.txt")
        data = {
            "age": 1,
            "file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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
            {
                "type": "fieldset",
                "key": "aFieldset",
                "components": [
                    {"key": "age", "type": "number"},
                    {
                        "key": "file",
                        "type": "file",
                        "file": {"name": "test.txt"},
                    },
                ],
            }
        ]
        form_step = FormStepFactory.create(
            form=upload.submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=upload.submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], True)  # created new
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_malformed_file(self, resize_mock):
        data = {
            "my_file": [{"malformed": "No 'url' for the file!"}],
        }
        components = [
            {"key": "my_file", "type": "file", "file": {"name": "test.txt"}},
        ]
        form_step = FormStepFactory.create(
            form_definition__configuration={"components": components}
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission__form=form_step.form, data=data
        )

        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(0, len(result))

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_uploads_to_submission_step_with_nested_fields(self, resize_mock):
        submission = SubmissionFactory.create()
        upload_in_repeating_group_1, upload_in_repeating_group_2, nested_upload = (
            TemporaryFileUploadFactory.create_batch(3, submission=submission)
        )
        data = {
            "repeatingGroup": [
                {
                    "fileInRepeatingGroup": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                    ]
                },
                {
                    "fileInRepeatingGroup": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                    ]
                },
            ],
            "nested": {
                "file": [
                    {
                        "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
                        "data": {
                            "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
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
            },
        }
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "components": [{"type": "file", "key": "fileInRepeatingGroup"}],
            },
            {"key": "nested.file", "type": "file"},
        ]
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 3)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 3)

        attachments_repeating_group = submission_step.attachments.filter(
            submission_variable__key="repeatingGroup"
        )

        self.assertEqual(2, attachments_repeating_group.count())

        attachments_repeating_group = submission_step.attachments.filter(
            submission_variable__key="nested.file"
        )

        self.assertEqual(1, attachments_repeating_group.count())

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_uploads_to_submission_step_with_nested_fields_with_matching_keys(
        self, resize_mock
    ):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "components": [
                            {
                                "type": "file",
                                "key": "attachment",
                                "registration": {
                                    "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                                },
                            }
                        ],
                    },
                    {
                        "key": "attachment",
                        "type": "file",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/456-456-456"
                        },
                    },
                ]
            },
        )
        form_step = submission.form.formstep_set.get()
        attachment_1 = TemporaryFileUploadFactory.create(
            submission=submission, file_name="attachmentInside.pdf"
        )
        attachment_2 = TemporaryFileUploadFactory.create(
            submission=submission, file_name="attachmentOutside.pdf"
        )
        data = {
            "repeatingGroup": [
                {
                    "attachment": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{attachment_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{attachment_1.uuid}",
                                "form": "",
                                "name": "attachmentInside.pdf",
                                "size": 46114,
                                "baseUrl": "http://server",
                                "project": "",
                            },
                            "name": "attachmentInside.pdf",
                            "size": 46114,
                            "type": "image/jpg",
                            "storage": "url",
                            "originalName": "attachmentInside.pdf",
                        }
                    ]
                }
            ],
            "attachment": [
                {
                    "url": f"http://server/api/v2/submissions/files/{attachment_2.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{attachment_2.uuid}",
                        "form": "",
                        "name": "attachmentOutside.pdf",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "attachmentOutside.pdf",
                    "size": 46114,
                    "type": "image/jpg",
                    "storage": "url",
                    "originalName": "attachmentOutside.pdf",
                }
            ],
        }
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
        )

        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 2)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

        # TODO can't get the attachment based on the submission variable, because both are wrongly related to the
        # attachment variable
        attachment_repeating_group = submission_step.attachments.get(
            original_name="attachmentInside.pdf"
        )

        self.assertEqual(
            attachment_repeating_group.informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123",
        )

        attachment = submission_step.attachments.get(
            original_name="attachmentOutside.pdf"
        )

        self.assertEqual(
            attachment.informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/456-456-456",
        )

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_multiple_uploads_to_submission_step_in_repeating_group(
        self, resize_mock
    ):
        submission = SubmissionFactory.create()
        upload_in_repeating_group_1, upload_in_repeating_group_2 = (
            TemporaryFileUploadFactory.create_batch(2, submission=submission)
        )
        data = {
            "repeatingGroup": [
                {
                    "fileInRepeatingGroup1": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
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
                    "fileInRepeatingGroup2": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                },
            ],
        }
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "components": [
                    {"type": "file", "key": "fileInRepeatingGroup1"},
                    {"type": "file", "key": "fileInRepeatingGroup2"},
                ],
            },
        ]
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 2)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

        self.assertTrue(
            submission_step.attachments.filter(
                submission_variable__key="repeatingGroup",
                _component_configuration_path="components.0.components.0",
            ).exists()
        )
        self.assertTrue(
            submission_step.attachments.filter(
                submission_variable__key="repeatingGroup",
                _component_configuration_path="components.0.components.1",
            ).exists()
        )

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_uploads_to_submission_step_with_nested_fields_to_register(
        self, resize_mock
    ):
        submission = SubmissionFactory.create()
        upload_in_repeating_group_1, upload_in_repeating_group_2, nested_upload = (
            TemporaryFileUploadFactory.create_batch(3, submission=submission)
        )
        data = {
            "repeatingGroup": [
                {
                    "fileInRepeatingGroup1": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
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
                    "fileInRepeatingGroup2": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_1.uuid}",
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
                },
                {
                    "fileInRepeatingGroup1": [
                        {
                            "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
                            "data": {
                                "url": f"http://server/api/v2/submissions/files/{upload_in_repeating_group_2.uuid}",
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
                    ]
                },
            ],
            "nested": {
                "file": [
                    {
                        "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
                        "data": {
                            "url": f"http://server/api/v2/submissions/files/{nested_upload.uuid}",
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
            },
        }
        components = [
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "components": [
                    {
                        "type": "file",
                        "key": "fileInRepeatingGroup1",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                        },
                    },
                    {
                        "type": "file",
                        "key": "fileInRepeatingGroup2",
                        "registration": {
                            "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/456-456-456"
                        },
                    },
                ],
            },
            {
                "key": "nested.file",
                "type": "file",
                "registration": {
                    "informatieobjecttype": "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123"
                },
            },
        ]
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 4)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 4)

        attachments_repeating_group_1 = submission_step.attachments.filter(
            submission_variable__key="repeatingGroup",
            _component_configuration_path="components.0.components.0",
        ).order_by("_component_data_path")

        self.assertEqual(
            attachments_repeating_group_1[0].informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123",
        )
        self.assertEqual(
            attachments_repeating_group_1[0]._component_data_path,
            "repeatingGroup.0.fileInRepeatingGroup1",
        )
        self.assertEqual(
            attachments_repeating_group_1[1].informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123",
        )
        self.assertEqual(
            attachments_repeating_group_1[1]._component_data_path,
            "repeatingGroup.1.fileInRepeatingGroup1",
        )

        attachments_repeating_group_2 = submission_step.attachments.filter(
            submission_variable__key="repeatingGroup",
            _component_configuration_path="components.0.components.1",
        )
        self.assertEqual(
            attachments_repeating_group_2[0].informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/456-456-456",
        )
        self.assertEqual(
            attachments_repeating_group_2[0]._component_data_path,
            "repeatingGroup.0.fileInRepeatingGroup2",
        )

        attachments_nested = submission_step.attachments.filter(
            submission_variable__key="nested.file"
        )

        self.assertEqual(
            attachments_nested[0].informatieobjecttype,
            "http://oz.nl/catalogi/api/v1/informatieobjecttypen/123-123-123",
        )
        self.assertEqual(attachments_nested[0]._component_data_path, "nested.file")

    @patch("openforms.submissions.tasks.resize_submission_attachment.delay")
    def test_attach_multiple_uploads_to_submission_step(self, resize_mock):
        submission = SubmissionFactory.create()
        upload_1 = TemporaryFileUploadFactory.create(
            file_name="my-image-1.jpg", submission=submission
        )
        upload_2 = TemporaryFileUploadFactory.create(
            file_name="my-image-2.jpg", submission=submission
        )
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
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
                    "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
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
            form=submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
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

        # test linking variables
        self.assertIsNotNone(attachment_1.submission_variable)
        self.assertEqual(attachment_1.submission_variable.key, "my_file")

        self.assertIsNotNone(attachment_2.submission_variable)
        self.assertEqual(attachment_2.submission_variable.key, "my_file")

        # expect we linked the same variable because we're testing a multiple=True field
        self.assertEqual(
            attachment_1.submission_variable.id, attachment_2.submission_variable.id
        )

        # test attaching again is idempotent
        result = attach_uploads_to_submission_step(submission_step)
        resize_mock.assert_not_called()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], False)  # not created
        self.assertEqual(result[1][1], False)  # not created
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

    @tag("gh-4197")  # Test tweaked to test with multiple images
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_attach_uploads_to_submission_step_resizes_images(self):
        submission = SubmissionFactory.create()
        upload_1 = TemporaryFileUploadFactory.create(
            file_name="my-image-1.png",
            content=File(open(self.test_image_path, "rb")),
            submission=submission,
        )
        upload_2 = TemporaryFileUploadFactory.create(
            file_name="my-image-2.png",
            content=File(open(self.test_image_path, "rb")),
            submission=submission,
        )
        data = {
            "my_normal_key": "foo",
            "my_file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_1.uuid}",
                        "form": "",
                        "name": "my-image-1.png",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-1-12305610-2da4-4694-a341-ccb919c3d543.png",
                    "size": 46114,
                    "type": "image/png",
                    "storage": "url",
                    "originalName": "my-image-1.png",
                },
                {
                    "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload_2.uuid}",
                        "form": "",
                        "name": "my-image-2.png",
                        "size": 46114,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    "name": "my-image-2-24836b01-012f-4886-be71-34f980c7d668.png",
                    "size": 46114,
                    "type": "image/png",
                    "storage": "url",
                    "originalName": "my-image-2.png",
                },
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
                "multiple": True,
            },
        ]
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=submission, data=data
        )

        # test attaching the file
        with self.captureOnCommitCallbacks(execute=True):
            result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 2)
        # assert both are created
        self.assertEqual(result[0][1], True)
        self.assertEqual(result[1][1], True)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 2)

        # verify resize
        attachment_1, attachment_2 = submission_step.attachments.all()
        self.assertEqual(attachment_1.form_key, "my_file")
        self.assertEqual(attachment_1.original_name, "my-image-1.png")
        self.assertImageSize(attachment_1.content, 100, 100, "png")

        self.assertEqual(attachment_2.form_key, "my_file")
        self.assertEqual(attachment_2.original_name, "my-image-2.png")
        self.assertImageSize(attachment_2.content, 100, 100, "png")

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

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": components},
            completed=False,
            with_report=False,
        )

        upload = TemporaryFileUploadFactory.create(
            submission=submission,
            file_name="aaa.txt",
            content__data=b"a" * 20,
            file_size=20,
        )

        data = {
            "my_file": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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

        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data=data,
        )

        with self.assertRaises(RequestEntityTooLarge):
            attach_uploads_to_submission_step(submission_step)

    @disable_admin_mfa()
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

    def test_attach_file_with_hidden_repeating_group(self):
        upload = TemporaryFileUploadFactory.create()
        data = {
            "someAttachment": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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
            ]
        }
        components = [
            {
                "type": "file",
                "key": "someAttachment",
            },
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "hidden": True,
                "components": [
                    {
                        "type": "textfield",
                        "key": "someTextField",
                    },
                ],
            },
        ]
        form_step = FormStepFactory.create(
            form=upload.submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=upload.submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 1)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

    def test_combination_attachment_and_repeating_group_with_numbers(self):
        upload = TemporaryFileUploadFactory.create()
        data = {
            "someAttachment": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
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
            "repeatingGroup": [
                {"someNumber": 10},
            ],
        }
        components = [
            {
                "type": "file",
                "key": "someAttachment",
            },
            {
                "key": "repeatingGroup",
                "type": "editgrid",
                "components": [
                    {
                        "type": "number",
                        "key": "someNumber",
                    },
                ],
            },
        ]
        form_step = FormStepFactory.create(
            form=upload.submission.form,
            form_definition__configuration={"components": components},
        )
        submission_step = SubmissionStepFactory.create(
            form_step=form_step, submission=upload.submission, data=data
        )

        # test attaching the file
        result = attach_uploads_to_submission_step(submission_step)

        self.assertEqual(len(result), 1)
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

    def test_attachment_applies_filename_template(self):
        components = [
            {
                "key": "someFile",
                "file": {
                    "name": "prefix_{{ fileName }}_postfix",
                },
                "type": "file",
            }
        ]
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": components},
        )

        upload = TemporaryFileUploadFactory.create(
            submission=submission,
            file_name="pixel.gif",
        )

        data = {
            "someFile": [
                {
                    "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                    "data": {
                        "url": f"http://server/api/v2/submissions/files/{upload.uuid}",
                        "form": "",
                        "name": "pixel.gif",
                        "size": upload.file_size,
                        "baseUrl": "http://server",
                        "project": "",
                    },
                    # ignored formio generated data
                    # "name": "formio generated -guid- filename.foo",
                    # "size": upload.file_size,
                    # "type": "image/gif",
                    "storage": "url",
                    "originalName": "pixel.gif",
                }
            ],
        }

        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data=data,
        )

        result = attach_uploads_to_submission_step(submission_step)
        self.assertEqual(len(result), 1)

        attachment_filename = result[0][0].file_name

        self.assertEqual(attachment_filename, "prefix_pixel_postfix.gif")
