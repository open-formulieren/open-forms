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
            ValidationError, "The file 'pixel.png' is not a .png."
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
            ValidationError, "The file 'pixel.jpg' is not a .jpg."
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
            ValidationError, "The file 'pixel.gif' is not a valid file type."
        ):
            validator(self.CORRECT_GIF)

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
