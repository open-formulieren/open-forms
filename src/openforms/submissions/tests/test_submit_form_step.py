"""
Test submitting a single form step in a submission.

When a submission ("session") is started, the data for a single form step must be
submitted to a submission step. Existing data can be overwritten and new data is created
by using HTTP PUT.
"""
from django.test import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..attachments import (
    attach_uploads_to_submission_step,
    cleanup_submission_temporary_uploaded_files,
    resolve_uploads_from_data,
)
from ..models import SubmissionFileAttachment
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    TemporaryFileUploadFactory,
)
from .mixins import SubmissionsMixin


class FormStepSubmissionTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step1, cls.step2 = FormStepFactory.create_batch(2, form=cls.form)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

        # ensure there is a submission
        cls.submission = SubmissionFactory.create(form=cls.form)

    def test_create_step_data(self):
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step1.uuid,
            },
        )
        body = {"data": {"some": "example data"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission_step = self.submission.submissionstep_set.get()
        self.assertEqual(
            response.json(),
            {
                "id": str(submission_step.uuid),
                "slug": self.step1.form_definition.slug,
                "formStep": {
                    "index": 0,
                    "configuration": {
                        "components": [{"type": "test-component", "key": "test-key"}]
                    },
                },
                "data": {
                    "some": "example data",
                },
            },
        )
        self.assertEqual(submission_step.data, {"some": "example data"})

    def test_create_step_wrong_step_id(self):
        """
        Validate that the step UUID belongs to the submission form.
        """
        other_form_step = FormStepFactory.create()
        assert other_form_step.form != self.form
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": other_form_step.uuid,
            },
        )

        response = self.client.put(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_step_invalid_submission_id(self):
        """
        Validate that the user must "own" the submission.
        """
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step1.uuid,
            },
        )

        response = self.client.put(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_step_data(self):
        self._add_submission_to_session(self.submission)
        SubmissionStepFactory.create(
            submission=self.submission,
            form_step=self.step1,
        )
        submission_step = SubmissionStepFactory.create(
            submission=self.submission,
            data={"foo": "bar"},
            form_step=self.step2,
        )
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step2.uuid,
            },
        )
        body = {"data": {"modified": "data"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "id": str(submission_step.uuid),
                "slug": self.step2.form_definition.slug,
                "formStep": {
                    "index": 1,
                    "configuration": {
                        "components": [{"type": "test-component", "key": "test-key"}]
                    },
                },
                "data": {
                    "modified": "data",
                },
            },
        )
        submission_step.refresh_from_db()
        self.assertEqual(submission_step.data, {"modified": "data"})

    def test_data_not_underscored(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "countryOfResidence",  # CamelCase
                        "type": "textfield",
                        "label": "Country of residence",
                    }
                ]
            }
        )
        form_step = FormStepFactory.create(form_definition=form_definition)

        submission = SubmissionFactory.create(form=form_step.form)
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )
        body = {"data": {"countryOfResidence": "Netherlands"}}

        response = self.client.put(endpoint, body)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        saved_data = submission.submissionstep_set.get().data

        # Check that the data has not been converted to snake case
        self.assertIn("countryOfResidence", saved_data)
        self.assertNotIn("country_of_residence", saved_data)


class SubmissionAttachmentTest(TestCase):
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

        # cleanup tested elsewhere
        upload.delete()

    def test_attach_uploads_to_submission_step(self):
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
            {"key": "my_file", "type": "file"},
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

        attachment = submission_step.attachments.get()
        self.assertEqual(attachment.form_key, "my_file")
        self.assertEqual(attachment.original_name, "my-image.jpg")
        self.assertEqual(attachment.content.read(), b"content")
        self.assertEqual(attachment.content_type, upload.content_type)
        self.assertEqual(attachment.temporary_file, upload)

        # test attaching again is idempotent
        result = attach_uploads_to_submission_step(submission_step)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], False)  # not created
        self.assertEqual(SubmissionFileAttachment.objects.count(), 1)

        # test cleanup
        cleanup_submission_temporary_uploaded_files(submission_step.submission)
        attachment.refresh_from_db()
        self.assertEqual(attachment.temporary_file, None)
        # verify the new FileField has its own content
        self.assertEqual(attachment.content.read(), b"content")

        attachment.delete()
