from datetime import date, datetime, time

from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy as _

from ...service import format_value
from .utils import load_json


class DefaultFormatterTestCase(SimpleTestCase):
    def test_formatters(self):
        # TODO ditch all_components*.json stuff after #1301 is fixed
        all_components = load_json("all_components.json")["components"]
        data = load_json("all_components_data.json")

        # Submission data should be native Python objects
        data["date"] = date.fromisoformat(data["date"])
        data["time"] = time.fromisoformat(data["time"])
        data["dateTime"] = datetime.fromisoformat(data["dateTime"])

        expected = {
            "bsn": "123456782",
            "date": "24 december 2021",
            "dateTime": "18 januari 2023 16:00",
            "file": "",
            "iban": "RO09 BCYP 0000 0012 3456 7890",
            "time": "16:26",
            "email": "test@example.com",
            "radio": "Option 2",
            "mapPoint": "4.893164274470299, 52.36673378967122",
            "mapLineString": "[4.893, 52.366], [4.894, 52.367], [4.895, 52.368]",
            "mapPolygon": "[[4.893, 52.366], [4.893, 52.368], [4.895, 52.368], [4.895, 52.366]]",
            "number": "42,123",
            "select": "Option 1",
            "postcode": "1234 AA",
            "textArea": "Textarea test",
            # "signature": "data:image/png;base64,iVBO[truncated]",
            "textField": "Simple text input",
            "phoneNumber": "+31633924456",
            "selectBoxes": "Option 1; Option 2",
            "licenseplate": "1-AAA-BB",
            "addressNL": "1234AA 1",
            "partners": (
                "[{'bsn': '999970136', 'firstNames': 'Pia', 'initials': 'P.', "
                "'affixes': '', 'lastName': 'Pauw', 'dateOfBirth': '1989-04-01', "
                "'dateOfBirthPrecision': 'date'}]"
            ),
            "children": (
                "[{'bsn': '999970409', 'affixes': 'van', 'initials': 'P.', "
                "'lastName': 'Paassen', 'firstNames': 'Pero', 'dateOfBirth': '2023-02-01', "
                "'dateOfBirthPrecision': 'date', 'selected': False}]"
            ),
        }

        for component in all_components:
            with self.subTest(key=component["key"], type=component["type"]):
                self.assertEqual(
                    format_value(component, data[component["key"]]),
                    expected[component["key"]],
                )

    def test_formatter_multiple(self):
        # TODO simplify without reference to all_components.json
        all_components = load_json("all_components.json")["components"]
        time_component = next(
            component for component in all_components if component["key"] == "time"
        )
        time_component["multiple"] = True

        # The data we pass to the formatter should be native Python objects
        data = [time(16, 26), time(8, 42), time(23, 1)]

        formatted = format_value(time_component, data)

        expected = "16:26; 08:42; 23:01"
        self.assertEqual(formatted, expected)

    def test_formatter_empty_value(self):
        # TODO simplify without reference to all_components.json
        all_components = load_json("all_components.json")["components"]
        component = all_components[0]

        formatted = format_value(component, "")

        self.assertEqual(formatted, "")

    def run_test_cases(self, component, cases):
        for value, expected in cases:
            with self.subTest(value=value, expected=expected):
                actual = format_value(component, value)
                self.assertEqual(actual, expected)

    def test_formatter_number(self):
        component = {
            "type": "number",
        }
        expected = [
            ("", ""),
            (None, ""),
            (0, "0"),
            (1, "1"),
            (-1, "-1"),
            (1234.56, "1.234,56"),
        ]
        self.run_test_cases(component, expected)

    def test_formatter_checkbox(self):
        component = {
            "type": "checkbox",
        }
        yes, no, maybe = _("yes,no,maybe").split(",")
        expected = [
            ("", ""),
            (None, ""),
            (True, yes),
            (False, no),
        ]
        self.run_test_cases(component, expected)

    def test_formatter_currency_multiple(self):
        component = {
            "type": "currency",
            "multiple": True,
        }
        expected = [
            ([None], ""),
            ([0, 1, 2], "0,00; 1,00; 2,00"),
            ([1234.56, 1, 0], "1.234,56; 1,00; 0,00"),
        ]
        self.run_test_cases(component, expected)

    def test_signature_as_html(self):
        component = {
            "type": "signature",
            "multiple": False,
            "key": "signature",
        }
        value = "data:image/png;base64,iVBO[truncated]"

        formatted_html = format_value(component, value, as_html=True)

        self.assertHTMLEqual(
            formatted_html,
            f"""<img src="{value}" alt="{_("signature added")}" style="max-width: 100%;" />""",
        )

    def test_addressnl_missing_keys(self):
        component = {
            "type": "addressNL",
            "multiple": False,
            "key": "addressNL",
        }

        value = {"postcode": "1234AA", "houseNumber": "1"}
        formatted_html = format_value(component, value, as_html=True)
        self.assertHTMLEqual(
            formatted_html,
            "1234AA 1",
        )

    def test_addressnl_html(self):
        component = {
            "type": "addressNL",
            "key": "addressNL",
        }

        value = {
            "postcode": "1234AA",
            "houseNumber": "1",
            "streetName": "test",
            "houseLetter": "A",
            "houseNumberAddition": "DD",
            "city": "Amsterdam",
        }

        with self.subTest("as_html False"):
            formatted_value = format_value(component, value, as_html=False)

            self.assertEqual(
                formatted_value,
                "test 1A DD\n1234AA Amsterdam",
            )
        with self.subTest("as_html True"):
            formatted_html = format_value(component, value, as_html=True)

            self.assertHTMLEqual(
                formatted_html,
                "test 1A DD<br>1234AA Amsterdam",
            )
