from unittest import TestCase

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import activate, get_language

from rest_framework.exceptions import ValidationError

from .. import validators

PIXEL_GIF = b"GIF89a\x01\x00\x01\x00\x81\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x08\x04\x00\x01\x04\x04\x00;"
PIXEL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"


class MimeTypeValidatorTests(TestCase):
    CORRECT_GIF = SimpleUploadedFile("pixel.gif", PIXEL_GIF, content_type="image/gif")
    _original_language = get_language()

    def setUp(self):
        self.CORRECT_GIF.seek(0)

    def setUpClass():
        activate("en")

    def tearDownClass():
        activate(MimeTypeValidatorTests._original_language)

    def test_accepts_correct_mime_types(self):
        self.assertIs(
            validators.mime_type_validator(self.CORRECT_GIF), self.CORRECT_GIF
        )

    def test_content_inconsistent_with_mime_type(self):
        file = SimpleUploadedFile("pixel.png", PIXEL_GIF, content_type="image/png")
        with self.assertRaisesRegex(
            ValidationError, "The file 'pixel.png' is not a image/png."
        ):
            validators.mime_type_validator(file)

    def test_fallback_to_extension(self):
        file = SimpleUploadedFile(
            "pixel.jpg",
            PIXEL_PNG,
            content_type="application/octet-stream",  # Maybe client doesn't know
        )
        with self.assertRaisesRegex(
            ValidationError, "The file 'pixel.jpg' is not a .jpg."
        ):
            validators.mime_type_validator(file)

    def test_accepts_unknown_extensions(self):
        file = SimpleUploadedFile(
            "pixel.gif", PIXEL_GIF, content_type="application/octet-stream"
        )
        self.assertIs(validators.mime_type_validator(file), file)

    def test_star_wildcard_in_allowed_mimetypes(self):
        self.assertIs(
            validators.mime_type_validator({"*"})(self.CORRECT_GIF), self.CORRECT_GIF
        )

    def test_empty_allowed_mimetypes(self):
        self.assertIs(
            validators.mime_type_validator({})(self.CORRECT_GIF), self.CORRECT_GIF
        )

    def test_mime_type_in_allowed_mimetypes(self):
        self.assertIs(
            validators.mime_type_validator({"image/gif"})(self.CORRECT_GIF),
            self.CORRECT_GIF,
        )

    def test_mime_type_not_allowed(self):
        with self.assertRaisesRegex(
            ValidationError, "The file 'pixel.gif' is not a valid file type."
        ):
            validators.mime_type_validator({"image/png"})(self.CORRECT_GIF)
