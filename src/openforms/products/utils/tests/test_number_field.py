from django.test import TestCase

from ..entry import convert_json_schema_to_py


class NumberFieldTestCase(TestCase):
    def setUp(self):
        self.json_schema_integer = {
            "required": ["huis_nummer"],
            "properties": {
                "huis_nummer": {
                    "title": "home number",
                    "type": "integer",
                    "maximum": 1000,
                    "minimum": 1,
                }
            },
        }
        self.json_schema_number = {
            "required": ["prod_price"],
            "properties": {
                "prod_price": {
                    "title": "Price",
                    "type": "number",
                    "maximum": 1000.00,
                    "minimum": 0.01,
                }
            },
        }

    def test_integer(self):
        result = convert_json_schema_to_py(self.json_schema_integer)
        self.assertEqual(result["components"][0]["type"], "number")
        self.assertEqual(result["components"][0]["validate"]["required"], True)
        self.assertEqual(result["components"][0]["validate"]["max"], 1000)
        self.assertEqual(result["components"][0]["validate"]["min"], 1)
        self.assertEqual(result["components"][0].get("decimalLimit"), 0)

    def test_number(self):
        result = convert_json_schema_to_py(self.json_schema_number)
        self.assertEqual(result["components"][0]["type"], "number")
        self.assertEqual(result["components"][0]["validate"]["required"], True)
        self.assertEqual(result["components"][0]["validate"]["max"], 1000.00)
        self.assertEqual(result["components"][0]["validate"]["min"], 0.01)
        self.assertEqual(result["components"][0].get("decimalLimit"), None)
