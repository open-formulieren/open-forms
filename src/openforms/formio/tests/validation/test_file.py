from django.test import TestCase
from django.utils.translation import gettext_lazy as _

import factory
from furl import furl

from openforms.submissions.tests.factories import TemporaryFileUploadFactory

from ...typing import FileComponent
from .helpers import extract_error, validate_formio_data


class _SubmittedFileDataFactory(factory.DictFactory):
    url = factory.SelfAttribute("..url")
    form = ""
    name = factory.SelfAttribute("..name")
    size = factory.SelfAttribute("..size")
    baseUrl = factory.LazyAttribute(lambda d: furl(d.factory_parent.url).origin)
    project = ""


class SubmittedFileFactory(factory.DictFactory):
    name = factory.Sequence(lambda n: f"foo-{n}.bin")
    originalName = factory.LazyAttribute(lambda obj: obj.name)
    size = factory.Faker("pyint", min_value=1)
    storage = "url"
    type = "application/foo"
    url = "http://localhost/api/v2/submissions/files/123"
    data = factory.SubFactory(_SubmittedFileDataFactory)

    @factory.post_generation
    def with_temporary_upload(obj, create, extracted, **kwargs):
        if extracted:
            # The temporary upload was explicitly provided, read the necessary values from there
            temporary_upload = extracted
            obj["originalName"] = obj["data"]["name"] = temporary_upload.file_name
            obj["size"] = obj["data"]["size"] = temporary_upload.file_size
        else:
            create_temporary_upload = (
                TemporaryFileUploadFactory.create
                if create
                else TemporaryFileUploadFactory.build
            )
            temporary_upload = create_temporary_upload(
                file_name=obj["name"], file_size=obj["size"]
            )
        new_url = f"http://localhost/api/v2/submissions/files/{temporary_upload.uuid}"
        obj["url"] = obj["data"]["url"] = new_url


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

        is_valid, _ = validate_formio_data(component, {})

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

        is_valid, errors = validate_formio_data(component, {})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "required")

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

        is_valid, _ = validate_formio_data(
            component, {"foo": SubmittedFileFactory.create_batch(2)}
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

        is_valid, errors = validate_formio_data(
            component, {"foo": SubmittedFileFactory.create_batch(2)}
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

        is_valid, errors = validate_formio_data(
            component, {"foo": SubmittedFileFactory.create_batch(2)}
        )

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")


class FileValidationTests(TestCase):
    def test_different_data(self):
        """Test consistency between ``url/size`` and ``data.url/data.size``."""

        with self.subTest("url field"):
            data = SubmittedFileFactory.create()
            data["data"]["url"] = "http://example.com"

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], "url")
            self.assertEqual(error.code, "invalid")

        with self.subTest("size field"):
            data = SubmittedFileFactory.create()
            data["data"]["size"] = 0

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], "size")
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

    def test_does_not_match_upload_file_size(self):

        data = SubmittedFileFactory.create()
        data["size"] = 0
        data["data"]["size"] = 0

        is_valid, errors = validate_formio_data(DEFAULT_FILE_COMPONENT, {"foo": [data]})

        self.assertFalse(is_valid)
        error = extract_error(errors["foo"][0], "size")
        self.assertEqual(error.code, "invalid")
        self.assertEqual(error, _("Size does not match the uploaded file."))

    def test_does_not_match_upload_name(self):

        with self.subTest("originalName field"):
            data = SubmittedFileFactory.create()
            data["originalName"] = "unrelated"

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )

            self.assertFalse(is_valid)
            error = extract_error(errors["foo"][0], "originalName")
            self.assertEqual(error.code, "invalid")
            self.assertEqual(error, _("Name does not match the uploaded file."))

        with self.subTest("data.name field"):
            data = SubmittedFileFactory.create()
            data["data"]["name"] = "unrelated"

            is_valid, errors = validate_formio_data(
                DEFAULT_FILE_COMPONENT, {"foo": [data]}
            )
            self.assertFalse(is_valid)
            error = errors["foo"][0]["data"]["name"]
            self.assertEqual(error.code, "invalid")
            self.assertEqual(error, _("Name does not match the uploaded file."))

    def test_passes_validation(self):
        data = SubmittedFileFactory.create()

        is_valid, _ = validate_formio_data(DEFAULT_FILE_COMPONENT, {"foo": [data]})

        self.assertTrue(is_valid)
