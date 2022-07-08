from copy import deepcopy

from django.test import TestCase

from ..entry import convert_json_schema_to_py


class NumberFieldTestCase(TestCase):
    """
    test output of function 'convert_json_schema_to_py' by passing
    different  dicts  represting JSON schema of a single field
    with type number or integer
    """

    def setUp(self):
        super().setUp()
        self.json_schema = {
            "required": ["salary"],
            "properties": {
                "salary": {
                    "title": "Some data that can be a number or integer",
                    "maximum": 1000,
                    "minimum": 1,
                }
            },
        }

    def test_integer(self):
        json_schema_integer = deepcopy(self.json_schema)
        json_schema_integer["properties"]["salary"]["type"] = "integer"
        json_schema_integer["properties"]["salary"]["maximum"] = 1000
        json_schema_integer["properties"]["salary"]["minimum"] = 1

        result = convert_json_schema_to_py(json_schema_integer)

        self.assertEqual(result["components"][0]["type"], "number")
        self.assertEqual(result["components"][0]["validate"]["required"], True)
        self.assertEqual(result["components"][0]["validate"]["max"], 1000)
        self.assertEqual(result["components"][0]["validate"]["min"], 1)
        self.assertEqual(result["components"][0].get("decimalLimit"), 0)

    def test_number(self):
        json_schema_number = deepcopy(self.json_schema)
        json_schema_number["properties"]["salary"]["type"] = "number"
        json_schema_number["properties"]["salary"]["maximum"] = 1000.00
        json_schema_number["properties"]["salary"]["minimum"] = 0.01

        result = convert_json_schema_to_py(json_schema_number)

        self.assertEqual(result["components"][0]["type"], "number")
        self.assertEqual(result["components"][0]["validate"]["required"], True)
        self.assertEqual(result["components"][0]["validate"]["max"], 1000.00)
        self.assertEqual(result["components"][0]["validate"]["min"], 0.01)
        self.assertEqual(result["components"][0].get("decimalLimit"), None)
