from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files import File
from django.test import TestCase, tag
from django.utils.translation import gettext_lazy as _

from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.utils.serializer_helpers import ReturnDict

from openforms.config.models import GlobalConfiguration
from openforms.submissions.attachments import temporary_upload_uuid_from_url
from openforms.submissions.constants import UPLOADS_SESSION_KEY
from openforms.submissions.tests.factories import TemporaryFileUploadFactory
from openforms.typing import JSONValue

from ...typing import FileComponent
from ..factories import SubmittedFileFactory
from .helpers import extract_error, validate_formio_data as _validate_formio_data

TEST_FILES_DIR = Path(__file__).parents[1] / "files"


DEFAULT_FILE_COMPONENT: FileComponent = {
    "type": "file",
    "key": "foo",
    "label": "Test",
    "storage": "url",
    "url": "",
    "useConfigFiletypes": False,
    "filePattern": "",
    "file": {"allowedTypesLabels": []},
}


def validate_formio_data(
    component: FileComponent, data: JSONValue, session_uploads: list[str] = []
) -> tuple[bool, ReturnDict]:
    request = APIRequestFactory().put("/irrelevant")

    # Add a session to the request:
    middleware = SessionMiddleware(lambda x: None)  # type: ignore
    middleware.process_request(request)
    request.session[UPLOADS_SESSION_KEY] = [str(uuid) for uuid in session_uploads]

    return _validate_formio_data(component, data, extra_context={"request": request})


class FileValidationMaxFilesAndRequiredTests(TestCase):
    """Tests related to ``validate.required`` and ``maxNumberOfFiles``."""

    def test_file_not_required(self):
        component: FileComponent = {
            "type": "file",
            "key": "foo",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
        }

        with self.subTest("without any provided value"):
            is_valid, _ = validate_formio_data(component, {})

            self.assertTrue(is_valid)

        with self.subTest("with an empty provided value"):
            is_valid, _ = validate_formio_data(component, {"foo": []})

            self.assertTrue(is_valid)

    def test_file_required(self):
        component: FileComponent = {
            "type": "file",
            "key": "foo",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
            "validate": {"required": True},
        }

        with self.subTest("without any provided value"):
            is_valid, errors = validate_formio_data(component, {})

            self.assertFalse(is_valid)
            self.assertIn(component["key"], errors)
            error = extract_error(errors, component["key"])
            self.assertEqual(error.code, "required")

        with self.subTest("with an empty provided value"):
            is_valid, errors = validate_formio_data(component, {"foo": []})

            self.assertFalse(is_valid)
            self.assertIn(component["key"], errors)
            error = extract_error(errors, component["key"])
            self.assertEqual(error.code, "min_length")

    def test_file_multiple_with_max_files(self):
        component: FileComponent = {
            "type": "file",
            "key": "foo",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
            "multiple": True,
            "maxNumberOfFiles": 2,
        }

        submitted_files = SubmittedFileFactory.create_batch(2)

        is_valid, _ = validate_formio_data(
            component,
            {"foo": submitted_files},
            session_uploads=[
                temporary_upload_uuid_from_url(f["url"]) for f in submitted_files
            ],
        )

        self.assertTrue(is_valid)

    def test_file_multiple_false(self):
        component: FileComponent = {
            "type": "file",
            "key": "foo",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
            "multiple": False,
        }

        submitted_files = SubmittedFileFactory.create_batch(2)

        is_valid, errors = validate_formio_data(
            component,
            {"foo": submitted_files},
            session_uploads=[
                temporary_upload_uuid_from_url(f["url"]) for f in submitted_files
            ],
        )

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")

    def test_file_max_files(self):
        component: FileComponent = {
            "type": "file",
            "key": "foo",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
            "maxNumberOfFiles": 1,
        }

        submitted_files = SubmittedFileFactory.create_batch(2)

        is_valid, errors = validate_formio_data(
            component,
            {"foo": submitted_files},
            session_uploads=[
                temporary_upload_uuid_from_url(f["url"]) for f in submitted_files
            ],
        )

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")


class FileValidationTests(TestCase):
    def test_different_data(self):
        """Test consistency between ``url/size`` and ``data.url/data.size``."""

        NON_FIELD_ERRORS_KEY = api_settings.NON_FIELD_ERRORS_KEY

        with self.subTest("url field"):
            data = SubmittedFileFactory.create()
            data["data"]["url"] = "http://example.com"

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], NON_FIELD_ERRORS_KEY)
            self.assertEqual(error.code, "invalid")

        with self.subTest("size field"):
            data = SubmittedFileFactory.create()
            data["data"]["size"] = 0

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], NON_FIELD_ERRORS_KEY)
            self.assertEqual(error.code, "invalid")

        with self.subTest("name/originalName field"):
            data = SubmittedFileFactory.create()
            data["data"]["name"] = "unrelated"

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], NON_FIELD_ERRORS_KEY)
            self.assertEqual(error.code, "invalid")

    def test_no_temporary_upload(self):

        data = (
            SubmittedFileFactory.build()
        )  # Using `.build()` will not persist the `TemporaryFileUpload`.

        is_valid, errors = validate_formio_data(DEFAULT_FILE_COMPONENT, {"foo": [data]})

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"][0], "url")
        self.assertEqual(error.code, "invalid")
        self.assertEqual(error, _("Invalid URL."))

    def test_temporary_upload_not_owned(self):
        # `SubmittedFileFactory` will create a `TemporaryFileUploadFactory`,
        # but we will not add it to the session.
        data = SubmittedFileFactory.create()

        is_valid, errors = validate_formio_data(
            DEFAULT_FILE_COMPONENT, {"foo": [data]}, session_uploads=[]
        )

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"][0], "url")
        self.assertEqual(error.code, "invalid")
        self.assertEqual(error, _("Invalid URL."))

    def test_does_not_match_upload_file_size(self):

        data = SubmittedFileFactory.create()
        data["size"] = 0
        data["data"]["size"] = 0

        is_valid, errors = validate_formio_data(
            DEFAULT_FILE_COMPONENT,
            {"foo": [data]},
            session_uploads=[temporary_upload_uuid_from_url(data["url"])],
        )

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"][0], "size")
        self.assertEqual(error.code, "invalid")
        self.assertEqual(error, _("Size does not match the uploaded file."))

    def test_does_not_match_upload_name(self):

        data = SubmittedFileFactory.create()
        data["originalName"] = "unrelated"
        data["data"]["name"] = "unrelated"

        is_valid, errors = validate_formio_data(
            DEFAULT_FILE_COMPONENT,
            {"foo": [data]},
            session_uploads=[temporary_upload_uuid_from_url(data["url"])],
        )

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"][0], "originalName")
        self.assertEqual(error.code, "invalid")
        self.assertEqual(error, _("Name does not match the uploaded file."))

    def test_passes_validation(self):
        data = SubmittedFileFactory.create()

        is_valid, _ = validate_formio_data(
            DEFAULT_FILE_COMPONENT,
            {"foo": [data]},
            session_uploads=[temporary_upload_uuid_from_url(data["url"])],
        )

        self.assertTrue(is_valid)


class FileValidationMimeTypeTests(TestCase):

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
            "foo": [
                SubmittedFileFactory.create(
                    temporary_upload=upload1,
                    type="application/pdf",  # we are lying!
                ),
                SubmittedFileFactory.create(
                    temporary_upload=upload2,
                    type="application/pdf",  # we are lying!
                ),
            ],
        }

        component: FileComponent = {
            "key": "foo",
            "type": "file",
            "label": "Test",
            "multiple": True,
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "applicaton/pdf",
            "file": {"type": ["application/pdf"], "allowedTypesLabels": []},
        }

        is_valid, errors = validate_formio_data(
            component, data, session_uploads=[upload1.uuid, upload2.uuid]
        )
        self.assertFalse(is_valid)
        self.assertEqual(len(errors["foo"]), 2)

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
            "foo": [
                SubmittedFileFactory.create(temporary_upload=upload1, type="image/png"),
                SubmittedFileFactory.create(temporary_upload=upload2, type="image/png"),
            ],
        }

        component: FileComponent = {
            "key": "foo",
            "type": "file",
            "label": "Test",
            "multiple": True,
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "image/png,image/jpeg",
            "file": {"type": ["image/png", "image/jpeg"], "allowedTypesLabels": []},
        }

        is_valid, _ = validate_formio_data(
            component, data, session_uploads=[upload1.uuid, upload2.uuid]
        )
        self.assertTrue(is_valid)

    @tag("GHSA-h85r-xv4w-cg8g")
    def test_attach_upload_validates_file_content_types_implicit_wildcard(self):
        with open(TEST_FILES_DIR / "image-256x256.png", "rb") as infile:
            upload = TemporaryFileUploadFactory.create(
                file_name="my-img.png",
                content=File(infile),
                content_type="image/png",
            )

        data = {
            "foo": [
                SubmittedFileFactory.create(temporary_upload=upload, type="image/png"),
            ],
        }

        component: FileComponent = {
            "key": "foo",
            "type": "file",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
        }

        is_valid, _ = validate_formio_data(
            component, data, session_uploads=[upload.uuid]
        )
        self.assertTrue(is_valid)

    @tag("GHSA-h85r-xv4w-cg8g")
    def test_attach_upload_validates_file_content_types_wildcard(self):
        """
        Regression test for the initial CVE-2022-31041 patch.

        Assert that file uploads are allowed if the "All" file types in the file
        configuration tab is used, which presents as a '*' entry.
        """
        with open(TEST_FILES_DIR / "image-256x256.png", "rb") as infile:
            upload = TemporaryFileUploadFactory.create(
                file_name="my-img.png",
                content=File(infile),
                content_type="image/png",
            )

        data = {
            "foo": [
                SubmittedFileFactory.create(temporary_upload=upload, type="image/png"),
            ],
        }

        component: FileComponent = {
            "key": "foo",
            "type": "file",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": False,
            "filePattern": "*",
            "file": {"type": ["*"], "allowedTypesLabels": []},
        }

        is_valid, _ = validate_formio_data(
            component, data, session_uploads=[upload.uuid]
        )
        self.assertTrue(is_valid)

    @patch("openforms.formio.components.vanilla.GlobalConfiguration.get_solo")
    def test_attach_upload_validates_file_content_types_default_configuration(
        self, m_solo: Mock
    ):
        m_solo.return_value = GlobalConfiguration(
            form_upload_default_file_types=["application/pdf", "image/jpeg"],
        )

        with open(TEST_FILES_DIR / "image-256x256.png", "rb") as infile:
            upload = TemporaryFileUploadFactory.create(
                file_name="my-img.png",
                content=File(infile),
                content_type="image/png",
            )

        data = {
            "foo": [
                SubmittedFileFactory.create(temporary_upload=upload, type="image/png"),
            ],
        }

        component: FileComponent = {
            "key": "foo",
            "type": "file",
            "label": "Test",
            "storage": "url",
            "url": "",
            "useConfigFiletypes": True,
            "filePattern": "*",
            "file": {"type": ["*"], "allowedTypesLabels": []},
        }

        is_valid, errors = validate_formio_data(
            component, data, session_uploads=[upload.uuid]
        )
        self.assertFalse(is_valid)
        self.assertEqual(len(errors["foo"]), 1)
