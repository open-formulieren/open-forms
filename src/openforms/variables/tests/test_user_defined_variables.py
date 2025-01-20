from django.test import TestCase

from jsonschema import Draft202012Validator

from ..constants import FormVariableDataTypes
from ..service import get_json_schema_for_user_defined_variable


class UserDefinedVariablesValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def check_schema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.validator.check_schema(schema)

    def test_string(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.string)
        self.check_schema(base)

    def test_boolean(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.boolean)
        self.check_schema(base)

    def test_object(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.object)
        self.check_schema(base)

    def test_array(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.array)
        self.check_schema(base)

    def test_int(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.int)
        self.check_schema(base)

    def test_float(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.float)
        self.check_schema(base)

    def test_datetime(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.datetime)
        self.check_schema(base)

    def test_date(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.date)
        self.check_schema(base)

    def test_time(self):
        base = get_json_schema_for_user_defined_variable(FormVariableDataTypes.time)
        self.check_schema(base)
