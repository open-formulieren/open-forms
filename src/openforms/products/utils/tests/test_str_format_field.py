from django.test import TestCase

from ..entry import convert_json_schema_to_py


class SingleFieldsTestCase(TestCase):
    def setUp(self):

        self.json_schema_email = {
            "properties": {
                "customer_email": {
                    "title": "Your email",
                    "type": "string",
                    "format": "email",
                }
            },
            "required": ["customer_email"],
        }
        self.json_schema_date = {
            "required": ["expired"],
            "properties": {
                "expired_date": {
                    "title": "The End",
                    "type": "string",
                    "format": "date",
                    "description": "Date of expire",
                }
            },
        }
        self.json_schema_time = {
            "properties": {
                "question": {
                    "title": "May be to lunch",
                    "type": "string",
                    "format": "time",
                    "description": "To lunch or not to lunch?",
                    "default": "11:30",
                }
            },
        }
        self.json_schema_date_time = {
            "properties": {
                "birthday": {
                    "title": "birthday",
                    "type": "string",
                    "format": "date-time",
                    "description": "Sure you remember it? Throw a party then",
                    "default": "1900-00-00,11:30",
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

    def test_string_email(self):
        result = convert_json_schema_to_py(self.json_schema_email)
        self.assertEqual(result["components"][0]["type"], "email")
        self.assertEqual(result["components"][0]["key"], "customer_email")
        self.assertEqual(result["components"][0]["validate"].get("required"), True)

    def test_string_time(self):
        result = convert_json_schema_to_py(self.json_schema_time)
        self.assertEqual(result["components"][0]["type"], "time")
        self.assertEqual(result["components"][0]["key"], "question")
        self.assertEqual(result["components"][0]["defaultValue"], "11:30")

    def test_string_date(self):
        result = convert_json_schema_to_py(self.json_schema_date)
        self.assertEqual(result["components"][0]["type"], "day")
        self.assertEqual(result["components"][0]["key"], "expired_date")

    def test_string_date_time(self):
        result = convert_json_schema_to_py(self.json_schema_date_time)
        self.assertEqual(result["components"][0]["type"], "datetime")
        self.assertEqual(result["components"][0]["key"], "birthday")
        self.assertEqual(result["components"][0]["input"], True)
        self.assertEqual(result["components"][0]["defaultValue"], "1900-00-00,11:30")
