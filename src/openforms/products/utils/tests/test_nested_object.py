from django.test import TestCase

from ..entry import convert_json_schema_to_py


class NumberFieldTestCase(TestCase):
    def setUp(self):
        self.json_schema_nested_object = {
            "title": "person",
            "properties": {
                "user_info": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "object",
                            "properties": {
                                "last_name": {
                                    "type": "string",
                                    "maxLength": 250,
                                },
                                "first_name": {"type": "string", "maxLength": 250},
                            },
                            "required": ["first_name", "last_name"],
                        },
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["email"],
                }
            },
        }

    def test_nested_object(self):
        result = convert_json_schema_to_py(self.json_schema_nested_object)
        # root elem (fieldset)
        self.assertEqual(result["components"][0]["type"], "fieldset")
        self.assertEqual(result["components"][0]["input"], False)
        self.assertEqual(result["components"][0]["key"], "user_info")

        # email = not nested single field
        self.assertEqual(result["components"][0]["components"][1]["key"], "email")
        self.assertEqual(result["components"][0]["components"][1]["input"], True)
        self.assertEqual(
            result["components"][0]["components"][1]["validate"].get("required"), True
        )

        # user_info = nested elem (fieldset) includes 2 textfields( see below)
        self.assertEqual(result["components"][0]["components"][0]["key"], "name")
        self.assertEqual(result["components"][0]["components"][0]["input"], False)
        self.assertEqual(result["components"][0]["components"][0]["type"], "fieldset")

        # testing nested content of user_info: first_name and last_name
        base = result["components"][0]["components"][0]["components"]
        # first_name
        self.assertEqual(base[0]["input"], True)
        self.assertEqual(base[0]["type"], "textfield")
        self.assertEqual(base[0]["validate"].get("required"), True)
        # last_name
        self.assertEqual(base[0]["type"], "textfield")
        self.assertEqual(base[1]["input"], True)
        self.assertEqual(base[1]["validate"].get("required"), True)
