import base64

from django.test import SimpleTestCase, tag

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class SignatureValidationTests(SimpleTestCase):
    def test_signature_field_required_validation(self):
        component: Component = {
            "type": "signature",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "blank"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    @tag("ghsa-9wxh-2452-43g8", "security-44")
    def test_signature_field_value_validation(self):
        component: Component = {
            "type": "signature",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        invalid_values = [
            # Url values
            ({"foo": "http://example.com"}, "invalid"),
            ({"foo": "http://example.com/image.png"}, "invalid"),
            ({"foo": "http://testserver/static/img/digid-46x46.png"}, "invalid"),
            # Plain text data URLs
            ({"foo": "data:,Hello%2C%20World%21"}, "invalid"),
            ({"foo": "data:text/plain,Hello%2C%20%57%6F%72%6C%64%21"}, "invalid"),
            # HTML data URLs
            (
                {"foo": "data:text/html,%3Ch1%3EHello%2C%20World%21%3C%2Fh1%3E"},
                "invalid",
            ),
            (
                {
                    "foo": "data:text/html,%3Cscript%3Ealert%28%27hi%27%29%3B%3C%2Fscript%3E"
                },
                "invalid",
            ),
            # Non-PNG image data URLs
            ({"foo": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEU"}, "invalid"),
            # Missing "base64" segment in data URLs
            ({"foo": "data:image/png,iVBORw0KGgoAAAANSUhEU"}, "invalid"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    @tag("ghsa-9wxh-2452-43g8", "security-44")
    def test_signature_field_with_valid_base64_png_image_value(self):
        component: Component = {
            "type": "signature",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        single_pixel_data = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
            b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
            b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
        ).decode("ascii")
        data_url = f"data:image/png;base64,{single_pixel_data}"

        is_valid, _ = validate_formio_data(component, {"foo": data_url})
        self.assertTrue(is_valid)
