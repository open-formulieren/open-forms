from django.test import TestCase

from jsonschema import Draft202012Validator

from ..constants import DATA_TYPE_TO_JSON_SCHEMA


class DataTypeValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def assertValidSchema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.assertIn("type", schema)
        self.validator.check_schema(schema)

    def test_all(self):
        for data_type, schema in DATA_TYPE_TO_JSON_SCHEMA.items():
            with self.subTest(data_type):
                self.assertValidSchema(schema)
