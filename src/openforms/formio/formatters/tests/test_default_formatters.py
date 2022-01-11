import json
import os

from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from ..service import format_value

FILES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files",
)


def load_json(filename: str):
    with open(os.path.join(FILES_DIR, filename), "r") as infile:
        return json.load(infile)


class DefaultFormatterTestCase(TestCase):
    def test_formatters(self):
        all_components = load_json("all_components.json")["components"]
        data = load_json("all_components_data.json")
        expected = {
            "bsn": "123456782",
            # "map": "52.3782943985417, 4.899629917973432",
            "date": "24 december 2021",
            "file": "leeg",
            "iban": "RO09 BCYP 0000 0012 3456 7890",
            "time": "16:26",
            "email": "test@example.com",
            "radio": "Option 2",
            "number": "42.123",
            "select": "Option 1",
            "password": "\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF",
            "postcode": "1234 AA",
            "textArea": "Textarea test",
            # "signature": "data:image/png;base64,iVBO[truncated]",
            "textField": "Simple text input",
            "phoneNumber": "+31633924456",
            "selectBoxes": "Option 1, Option 2",
            "licenseplate": "1-AAA-BB",
            "select2": "29 december 2021",
            "select3": "08:15",
        }

        for component in all_components:
            with self.subTest(type=component["type"]):
                self.assertEqual(
                    format_value(component, data[component["key"]]),
                    expected[component["key"]],
                )

    def test_formatter_multiple(self):
        all_components = load_json("all_components.json")["components"]
        time_component = next(
            (component for component in all_components if component["key"] == "time")
        )
        time_component["multiple"] = True

        data = ["16:26:00", "8:42:00", "23:01:00"]

        formatted = format_value(time_component, data)

        expected = "16:26, 08:42, 23:01"
        self.assertEqual(formatted, expected)

    def test_formatter_empty_value(self):
        all_components = load_json("all_components.json")["components"]
        component = all_components[0]

        formatted = format_value(component, "")

        self.assertEqual(formatted, "")

    def test_formatter_checkbox(self):
        component = {
            "type": "checkbox",
            "label": "Some checkbox",
            "multiple": False,
        }
        yes, no, maybe = _("yes,no,maybe").split(",")
        expected = [
            (True, yes),
            (False, no),
        ]

        for value, expected_formatted in expected:
            with self.subTest(value=value, expected=expected_formatted):
                formatted = format_value(component, value)

                self.assertEqual(formatted, expected_formatted)
