from copy import deepcopy

from django.test import TestCase

from ..entry import convert_json_schema_to_py


class EnumPresenceTestCase(TestCase):
    """
    test output of function 'convert_json_schema_to_py' by passing
    different  enums present in JSON schema: primitive(unique-choice) and array(muliple-choices)
    """

    def setUp(self):
        super().setUp()
        self.json_schema = {
            "properties": {
                "reden": {
                    "title": "Reden",
                    "description": "Few words",
                }
            },
        }
        self.values_primitive = [
            {"label": "werk", "value": "werk"},
            {"label": "woning", "value": "woning"},
            {
                "label": "ondersteuning",
                "value": "ondersteuning",
            },
        ]
        self.values_array = [
            {"label": "5", "value": "5"},
            {"label": "10", "value": "10"},
            {"label": "15", "value": "15"},
        ]

    def test_primitive_enum(self):
        """func output containes items from JSON schema(enum unique choice) in key 'data'"""
        json_schema = deepcopy(self.json_schema)
        json_schema["properties"]["reden"]["type"] = "string"
        json_schema["properties"]["reden"]["enum"] = ["werk", "woning", "ondersteuning"]

        result = convert_json_schema_to_py(json_schema)

        self.assertEqual(
            result["components"][0]["data"]["values"], self.values_primitive
        )
        self.assertEqual(result["components"][0]["dataType"], "string")

    def test_array_enum(self):
        """func output containes items from JSON schema (enum multiple choice) in key 'values'"""
        json_schema = deepcopy(self.json_schema)
        json_schema["properties"]["reden"]["type"] = "array"
        json_schema["properties"]["reden"]["items"] = {
            "type": "number",
            "enum": ["5", "10", "15"],
        }

        result = convert_json_schema_to_py(json_schema)

        self.assertEqual(result["components"][0]["values"], self.values_array)
