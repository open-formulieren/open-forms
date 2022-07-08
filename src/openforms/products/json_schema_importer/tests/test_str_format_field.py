from copy import deepcopy

from django.test import TestCase

from ..entry import convert_json_schema_to_py


class SingleFieldsTestCase(TestCase):
    """
    test output of function 'convert_json_schema_to_py' by passing
    different  dicts  represting JSON schema of a single field
    with type string but different formats
    """

    def setUp(self):
        super().setUp()
        self.json_schema = {
            "properties": {
                "customer_data": {
                    "title": "Some data that can be changed in tests but it's always a string",
                    "type": "string",
                }
            },
            "required": ["customer_data"],
        }

    def test_string_email(self):
        json_schema_email = deepcopy(self.json_schema)
        json_schema_email["properties"]["customer_data"]["format"] = "email"

        result = convert_json_schema_to_py(json_schema_email)

        self.assertEqual(result["components"][0]["type"], "email")
        self.assertEqual(result["components"][0]["key"], "customer_data")
        self.assertEqual(result["components"][0]["validate"].get("required"), True)

    def test_string_time(self):
        json_schema_time = deepcopy(self.json_schema)
        json_schema_time["properties"]["customer_data"]["format"] = "time"
        json_schema_time["properties"]["customer_data"]["default"] = "11:30"

        result = convert_json_schema_to_py(json_schema_time)

        self.assertEqual(result["components"][0]["type"], "time")
        self.assertEqual(result["components"][0]["defaultValue"], "11:30")

    def test_string_date_time(self):
        json_schema_date_time = deepcopy(self.json_schema)
        json_schema_date_time["properties"]["customer_data"]["format"] = "date-time"
        json_schema_date_time["properties"]["customer_data"][
            "default"
        ] = "1900-00-00,11:30"

        result = convert_json_schema_to_py(json_schema_date_time)

        self.assertEqual(result["components"][0]["type"], "datetime")
        self.assertEqual(result["components"][0]["input"], True)
