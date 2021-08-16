from django.test import SimpleTestCase

from ..mixins import _camelize_required


class CamelizeTests(SimpleTestCase):
    def test_simple_unmodified(self):
        cases = [{}, {"foo": "bar"}]

        for case in cases:
            with self.subTest(case=case):
                result = _camelize_required(case)

                self.assertEqual(result, case)

    def test_simple_json_schema_without_required(self):
        schema = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "string",
                }
            },
        }

        result = _camelize_required(schema)

        self.assertEqual(result, schema)

    def test_simple_json_schema_with_required(self):
        schema = {
            "type": "object",
            "properties": {
                "fooBar": {
                    "type": "string",
                }
            },
            "required": ["foo_bar"],
        }

        result = _camelize_required(schema)

        self.assertEqual(
            result,
            {
                "type": "object",
                "properties": {
                    "fooBar": {
                        "type": "string",
                    }
                },
                "required": ["fooBar"],
            },
        )
