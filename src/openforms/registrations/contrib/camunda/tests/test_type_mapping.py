import json
import os
from datetime import date, datetime, time

from django.test import SimpleTestCase
from django.utils import timezone

from ..type_mapping import to_python

FILES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files",
)


def load_json(filename: str):
    with open(os.path.join(FILES_DIR, filename), "r") as infile:
        return json.load(infile)


class TypeMappingTests(SimpleTestCase):
    def test_all_types(self):
        all_components = load_json("all_components.json")["components"]
        data = load_json("all_components_data.json")
        expected = {
            "bsn": "123456782",
            "map": [52.3782943985417, 4.899629917973432],
            "date": date(2021, 12, 24),
            "file": [],
            "iban": "RO09 BCYP 0000 0012 3456 7890",
            "time": time(16, 26),
            "email": "test@example.com",
            "radio": "option2",
            "number": 42.123,
            "select": "option1",
            "password": "secret",
            "postcode": "1234 AA",
            "textArea": "Textarea test",
            "signature": "data:image/png;base64,iVBO[truncated]",
            "textField": "Simple text input",
            "phoneNumber": "+31633924456",
            "selectBoxes": ["option1", "option2"],
            "licenseplate": "1-AAA-BB",
            "select2": date(2021, 12, 29),
            "select3": datetime(2021, 12, 29, 7, 15).replace(tzinfo=timezone.utc),
        }

        for component in all_components:
            key = component["key"]
            value = data[key]
            expected_python_value = expected[key]

            with self.subTest(
                component=component["key"], value=value, expected=expected_python_value
            ):
                result = to_python(component, value)

                self.assertEqual(result, expected_python_value)

    def test_multiple_component(self):
        component = {
            "type": "number",
            "multiple": True,
        }

        result = to_python(component, [42, 420.69])

        self.assertEqual(result, [42, 420.69])

    def test_appointment_select_product(self):
        component = {
            "type": "select",
            "appointments": {
                "showProducts": True,
            },
        }
        value = {"name": "Example name", "identifier": "123"}

        result = to_python(component, value)

        self.assertEqual(result, value)

    def test_partial_appointment_config(self):
        component = {"type": "select", "appointments": {"showDates": False}}
        value = "option1"

        result = to_python(component, value)

        self.assertEqual(result, "option1")
