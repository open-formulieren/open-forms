from copy import deepcopy

from django.test import TestCase

from ..entry import convert_json_schema_to_py


class SingleTextFieldTestCase(TestCase):
    """
    test output of function 'convert_json_schema_to_py' by passing
    different  dicts  represting JSON schema of a single field
    with type string but no format
    """

    def setUp(self):
        super().setUp()
        self.json_schema_string = {
            "properties": {
                "comment": {
                    "title": "Comment",
                    "type": "string",
                    "description": "Few words in short",
                }
            },
        }

    def test_simple_string(self):
        """func output has type of textarea if no validation keyword 'maxLength' present in JSON schema"""

        result = convert_json_schema_to_py(self.json_schema_string)

        self.assertEqual(result["components"][0]["key"], "comment")
        self.assertEqual(result["components"][0]["description"], "Few words in short")
        self.assertEqual(result["components"][0]["type"], "textarea")

    def test_string_textfield(self):
        """func output has type of textfield by presence of keyword 'maxLength' in JSON schema"""
        json_schema_textfield = deepcopy(self.json_schema_string)
        json_schema_textfield["properties"]["comment"]["maxLength"] = 250

        result = convert_json_schema_to_py(json_schema_textfield)

        self.assertEqual(result["components"][0]["key"], "comment")
        self.assertEqual(result["components"][0]["type"], "textfield")
        self.assertEqual(result["components"][0]["validate"].get("required"), False)
        self.assertEqual(result["components"][0]["validate"]["maxLength"], 250)

    def test_string_with_pattern(self):
        """func output has a certain pattern in validate dict"""
        json_schema_string_pattern = deepcopy(self.json_schema_string)
        json_schema_string_pattern["properties"]["comment"]["pattern"] = "^[A-Z]?$"

        result = convert_json_schema_to_py(json_schema_string_pattern)

        self.assertEqual(result["components"][0]["validate"].get("pattern"), "^[A-Z]?$")

    def test_string_required(self):
        """func output ....."""
        json_schema_required = deepcopy(self.json_schema_string)
        json_schema_required["required"] = ["comment"]

        result = convert_json_schema_to_py(json_schema_required)

        self.assertEqual(result["components"][0]["key"], "comment")
        self.assertEqual(result["components"][0]["validate"].get("required"), True)
