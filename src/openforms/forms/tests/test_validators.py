from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from openforms.formio.validators import validate_formio_js_schema


class FormioJSSchemaValidatorTests(SimpleTestCase):
    def test_valid_schemas(self):
        valid = [
            {"components": []},
            {
                "components": [
                    {
                        "type": "foo",
                        "components": [],
                    }
                ]
            },
        ]

        for schema in valid:
            with self.subTest(schema=schema):
                try:
                    validate_formio_js_schema(schema)
                except ValidationError as exc:
                    self.fail(f"Unexpected validation error: {exc}")

    def test_invalid_schemas(self):
        invalid = [
            {},
            [],
            None,
            {"anything": "else"},
            {"components": None},
            {"components": {}},
        ]

        for schema in invalid:
            with self.subTest(schema=schema):
                with self.assertRaises(ValidationError):
                    validate_formio_js_schema(schema)
