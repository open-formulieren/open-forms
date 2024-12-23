from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from rest_framework.exceptions import ValidationError

from ..api import validators

PIXEL_GIF = b"GIF89a\x01\x00\x01\x00\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x08\x04\x00\x01\x04\x04\x00;"
PIXEL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"

TEST_FILES = Path(__file__).parent.resolve() / "files"


class MimeTypeAllowedTests(SimpleTestCase):
    def test_mimetype_allowed_wildcard_patterns(self):
        patterns = (
            ("image/*", ("image/png", "image/jpg")),
            (
                "application/vnd.oasis.opendocument.*",
                ("application/vnd.oasis.opendocument.text",),
            ),
            ("application/foo-*", ("application/foo-bar",)),
            ("image*", ("image/png",)),
        )

        for pattern, mime_types in patterns:
            for mime_type in mime_types:
                with self.subTest(pattern=pattern, mime_type=mime_type):
                    allowed = validators.mimetype_allowed(mime_type, [], [pattern])

                    self.assertTrue(allowed)

    def test_mimetype_not_allowed_wildcard_patterns(self):
        patterns = (
            ("sub/match*", "pubsub/matchnotitshould"),
            ("/nonsense*", "absolute/nonsense"),
        )

        for pattern, mime_type in patterns:
            with self.subTest(pattern=pattern, mime_type=mime_type):
                allowed = validators.mimetype_allowed(mime_type, [], [pattern])

                self.assertFalse(allowed)


@override_settings(LANGUAGE_CODE="en")
class MimeTypeValidatorTests(SimpleTestCase):
    CORRECT_GIF = SimpleUploadedFile("pixel.gif", PIXEL_GIF, content_type="image/gif")

    def setUp(self):
        super().setUp()
        self.CORRECT_GIF.seek(0)

    def test_accepts_correct_mime_types(self):
        validator = validators.MimeTypeValidator()

        try:
            validator(self.CORRECT_GIF)
        except ValidationError as e:
            self.fail(f"Correct file failed validation: {e}")

    def test_content_inconsistent_with_mime_type(self):
        file = SimpleUploadedFile("pixel.png", PIXEL_GIF, content_type="image/png")
        validator = validators.MimeTypeValidator()

        with self.assertRaisesMessage(
            ValidationError, "The provided file is not a .png."
        ):
            validator(file)

    def test_fallback_to_extension(self):
        file = SimpleUploadedFile(
            "pixel.jpg",
            PIXEL_PNG,
            content_type="application/octet-stream",  # Maybe client doesn't know
        )
        validator = validators.MimeTypeValidator()

        with self.assertRaisesMessage(
            ValidationError, "The provided file is not a .jpg."
        ):
            validator(file)

    def test_accepts_unknown_extensions(self):
        # null-byte to force application/octet-stream mime detection and "???" extension
        file = SimpleUploadedFile(
            "pixel.gif", b"\x00asjdkfl", content_type="application/octet-stream"
        )
        validator = validators.MimeTypeValidator()

        try:
            validator(file)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_mime_type_inferred_from_magic(self):
        # gif works on Arch Linux, but not on Debian based systems, while PNG does work
        # on both
        file = SimpleUploadedFile(
            "pixel.png", PIXEL_PNG, content_type="application/octet-stream"
        )
        validator = validators.MimeTypeValidator()

        try:
            validator(file)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_unknown_file_type(self):
        file = SimpleUploadedFile(
            "unknown-type",
            b"test",
            content_type="application/octet-stream",  # see e2e test SingleFileTests.test_unknown_file_type
        )
        validator = validators.MimeTypeValidator(
            allowed_mime_types=None
        )  # allows any mime type

        with self.assertRaisesMessage(
            ValidationError,
            "Could not determine the file type. Please make sure the file name "
            "has an extension.",
        ):
            validator(file)

    def test_star_wildcard_in_allowed_mimetypes(self):
        validator = validators.MimeTypeValidator({"*"})

        try:
            validator(self.CORRECT_GIF)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_empty_allowed_mimetypes(self):
        validator = validators.MimeTypeValidator({})

        try:
            validator(self.CORRECT_GIF)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_mime_type_in_allowed_mimetypes(self):
        validator = validators.MimeTypeValidator({"image/gif"})

        try:
            validator(self.CORRECT_GIF)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_mime_type_not_allowed(self):
        validator = validators.MimeTypeValidator({"image/png"})

        with self.assertRaisesMessage(
            ValidationError, "The provided file is not a valid file type."
        ):
            validator(self.CORRECT_GIF)

    def test_mif1_brand_heif_files_are_acceptable_heic(self):
        # lib magic has a hard time recognizing the HEVC is used and a heif container actutally is heic
        validator = validators.MimeTypeValidator({"image/heic"})
        sample_1 = SimpleUploadedFile(
            "sample1.heic", b"\x00\x00\x00\x18ftypmif1", content_type="image/heif"
        )

        try:
            validator(sample_1)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_heic_brand_heif_files_are_recognized_as_heic(self):
        # lib magic has a hard time recognizing the HEVC is used and a heif container actutally is heic
        validator = validators.MimeTypeValidator({})  # accept any
        sample_2 = SimpleUploadedFile(
            "sample2.heic", b"\x00\x00\x00\x18ftypheic", content_type="image/heif"
        )

        try:
            validator(sample_2)
        except ValidationError as e:
            self.fail(f"Valid file failed validation: {e}")

    def test_heic_brand_heif_files_are_not_recognized_as_png(self):
        # lib magic has a hard time recognizing the HEVC is used and a heif container actutally is heic
        validator = validators.MimeTypeValidator({"image/png"})
        sample_2 = SimpleUploadedFile(
            "sample2.heic", b"\x00\x00\x00\x18ftypheic", content_type="image/heif"
        )

        with self.assertRaises(ValidationError):
            validator(sample_2)

    def test_multiple_valid_mimetypes_in_zip_files_are_transformed(self):
        valid_types = ("application/x-zip-compressed", "application/zip-compressed")
        legacy_zip_file = TEST_FILES / "test-zip.zip"
        validator = validators.MimeTypeValidator()

        for valid_type in valid_types:
            sample = SimpleUploadedFile(
                "test-zip.zip",
                legacy_zip_file.read_bytes(),
                content_type=valid_type,
            )

            validator(sample)

    def test_allowed_mime_types_for_csv_files(self):
        valid_types = ("text/csv", "text/plain")
        csv_file = TEST_FILES / "test-csv-file.csv"
        validator = validators.MimeTypeValidator()

        for valid_type in valid_types:
            sample = SimpleUploadedFile(
                "test-csv-file.csv",
                csv_file.read_bytes(),
                content_type=valid_type,
            )

            validator(sample)

    def test_allowed_mime_types_for_msg_files(self):
        valid_type = "application/vnd.ms-outlook"
        msg_file = TEST_FILES / "test.msg"
        validator = validators.MimeTypeValidator(allowed_mime_types=[valid_type])

        # 4795
        # The sdk cannot determine the content_type for .msg files correctly.
        # Because .msg is a windows specific file, and linux and MacOS don't know it.
        # So we simulate the scenario where content_type is unknown
        sample = SimpleUploadedFile(
            name="test.msg",
            content=msg_file.read_bytes(),
            content_type="",  # replicate the behaviour of the frontend
        )

        validator(sample)

    def test_validate_files_multiple_mime_types(self):
        """Assert that validation of files associated with multiple mime types works

        A refactoring of `MimeTypeValidator` broke validation for files where the
        admissible types are specified in the form 'mime1,mime2,mime3'.

        GH #2577"""

        odt_file = TEST_FILES / "test.odt"

        file = SimpleUploadedFile(
            "test.odt",
            odt_file.read_bytes(),
            content_type="application/vnd.oasis.opendocument.text",
        )

        validator = validators.MimeTypeValidator(
            [
                "application/vnd.oasis.opendocument.*,application/vnd.oasis.opendocument.text-template,",
                "application/pdf",
            ]
        )

        validator(file)
