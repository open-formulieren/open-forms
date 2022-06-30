from django.test import TestCase

from ..entry import convert_json_schema_to_py


class SingleTextFieldTestCase(TestCase):
    def setUp(self):
        self.json_schema_string = {
            "properties": {
                "comment": {
                    "title": "Comment",
                    "type": "string",
                    "description": "Few words in short",
                    "maxLength": 250,
                }
            },
        }
        self.json_schema_string_pattern = {
            "properties": {
                "kenteken": {
                    "title": "Kenteken",
                    "type": "string",
                    "pattern": "^[A-Z0-9]?$",
                    "description": "Aanvraag wordt gedaan.",
                    "maxLength": 250,
                }
            },
        }

        self.json_schema_textarea = {
            "required": [],
            "properties": {
                "review": {
                    "title": "User review",
                    "type": "string",
                    "description": "Product review",
                }
            },
        }

    def test_string(self):
        result = convert_json_schema_to_py(self.json_schema_string)
        self.assertEqual(result["components"][0]["type"], "textfield")
        self.assertEqual(result["components"][0]["key"], "comment")
        self.assertEqual(result["components"][0]["description"], "Few words in short")

    def test_string_with_pattern(self):
        result = convert_json_schema_to_py(self.json_schema_string_pattern)
        self.assertEqual(result["components"][0]["type"], "textfield")
        self.assertEqual(
            result["components"][0]["validate"].get("pattern"), "^[A-Z0-9]?$"
        )

    def test_string_textarea(self):
        result = convert_json_schema_to_py(self.json_schema_textarea)
        self.assertEqual(result["components"][0]["type"], "textarea")
        self.assertEqual(result["components"][0]["key"], "review")
        self.assertEqual(result["components"][0]["description"], "Product review")
        self.assertEqual(result["components"][0]["validate"].get("required"), False)
