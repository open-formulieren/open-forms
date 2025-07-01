import json
import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import timezone

from openforms.formio.formatters.tests.utils import load_json as formio_load_json

from ..type_mapping import to_python

FILES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files",
)


def load_json(filename: str, files_dir=FILES_DIR):
    with open(os.path.join(files_dir, filename)) as infile:
        return json.load(infile)


class TypeMappingTests(SimpleTestCase):
    def test_kitchensink_types(self):
        all_components = formio_load_json("kitchensink_components.json")["components"]
        data = formio_load_json("kitchensink_data_with_hidden.json")

        # formio doesn't submit anything for empty numeric fields
        # this is handled by the plugin calling merged_data.get(key, None) before the to_python() we're testing
        # so here we simulate that behaviour
        data["numberEmpty"] = None
        data["currencyEmpty"] = None

        skip_keys = [
            "updateNote",
        ]

        utc1_timezone = timezone.get_fixed_timezone(timedelta(hours=1))
        expected = {
            "bsn": "111222333",
            "bsnEmpty": "",
            "bsnHidden": "111222333",
            "bsnMulti": ["111222333", "123456782"],
            "bsnMultiEmpty": [None],
            "checkbox": True,
            "checkboxDefault": True,
            "checkboxEmpty": False,
            "checkboxHidden": True,
            "currency": Decimal("1234.56"),
            "currencyEmpty": None,
            "currencyHidden": Decimal("123"),
            "currencyDecimal": Decimal("1234.56"),
            "currencyDecimalHidden": Decimal("123.45"),
            "currencyDecimalMulti": [
                Decimal("1234.56"),
                Decimal("1"),
                Decimal("0"),
            ],
            "currencyMulti": [
                Decimal("1234.56"),
                Decimal("1"),
                Decimal("0"),
            ],
            "currencyMultiEmpty": [None],
            "date": date(2022, 2, 14),
            "dateEmpty": None,
            "dateHidden": date(2022, 2, 14),
            "dateMulti": [
                date(2022, 2, 14),
                date(2022, 2, 15),
                date(2022, 2, 16),
            ],
            "dateTime": datetime(2023, 1, 18, 16, tzinfo=utc1_timezone),
            "dateTimeMultipleEmpty": [None],
            "dateTimeEmpty": None,
            "dateTimeHidden": datetime(2023, 1, 18, 16, tzinfo=utc1_timezone),
            "dateTimeMultiple": [
                datetime(2023, 1, 18, 16, tzinfo=utc1_timezone),
                datetime(2023, 1, 19, 17, tzinfo=utc1_timezone),
                datetime(2023, 1, 20, 18, tzinfo=utc1_timezone),
            ],
            "dateMultiEmpty": [None],
            "email": "test@example.com",
            "emailEmpty": "",
            "emailHidden": "test@example.com",
            "emailMulti": ["aaa@aaa.nl", "bbb@bbb.nl"],
            "emailMultiDefault": ["aaa@aaa.nl", "bbb@bbb.nl"],
            "emailMultiEmpty": [None],
            "file": [
                {
                    "data": {
                        "baseUrl": "http://localhost:8000/api/v2/",
                        "form": "",
                        "name": "blank.doc",
                        "project": "",
                        "size": 1048576,
                        "url": "http://localhost:8000/api/v2/submissions/files/35527900-8248-4e75-a553-c2d1039a002b",
                    },
                    "name": "blank-65faf10b-afaf-48af-a749-ff5780abf75b.doc",
                    "originalName": "blank.doc",
                    "size": 1048576,
                    "storage": "url",
                    "type": "application/msword",
                    "url": "http://localhost:8000/api/v2/submissions/files/35527900-8248-4e75-a553-c2d1039a002b",
                }
            ],
            "fileUploadEmpty": [],
            "fileUploadHidden": [],
            "fileUploadMulti": [
                {
                    "data": {
                        "baseUrl": "http://localhost:8000/api/v2/",
                        "form": "",
                        "name": "blank.doc",
                        "project": "",
                        "size": 1048576,
                        "url": "http://localhost:8000/api/v2/submissions/files/a2444b75-dc1a-4363-a482-286579992768",
                    },
                    "name": "blank-428299d9-9aa3-4b31-a908-dc87f91ba1b0.doc",
                    "originalName": "blank.doc",
                    "size": 1048576,
                    "storage": "url",
                    "type": "application/msword",
                    "url": "http://localhost:8000/api/v2/submissions/files/a2444b75-dc1a-4363-a482-286579992768",
                },
                {
                    "data": {
                        "baseUrl": "http://localhost:8000/api/v2/",
                        "form": "",
                        "name": "dummy.doc",
                        "project": "",
                        "size": 1048576,
                        "url": "http://localhost:8000/api/v2/submissions/files/9ecc3688-5975-4b3f-b0e3-d312613fb6de",
                    },
                    "name": "dummy-82450592-32d1-4efa-b2f0-a0c024571df4.doc",
                    "originalName": "dummy.doc",
                    "size": 1048576,
                    "storage": "url",
                    "type": "application/msword",
                    "url": "http://localhost:8000/api/v2/submissions/files/9ecc3688-5975-4b3f-b0e3-d312613fb6de",
                },
            ],
            "fileUploadMultiEmpty": [],
            "iban": "NL02ABNA0123456789",
            "ibanEmpty": "",
            "ibanHidden": "NL02ABNA0123456789",
            "ibanMulti": ["NL02ABNA0123456789", "BE71096123456769"],
            "ibanMultiEmpty": [None],
            "licensePlateEmpty": "",
            "licensePlateHidden": "aa-bb-12",
            "licensePlateMulti": ["aa-bb-12", "1-aaa-12", "12-aa-34"],
            "licensePlateMultiEmpty": [None],
            "licenseplate": "aa-bb-12",
            "mapPoint": {
                "type": "Point",
                "coordinates": [52.373087283242505, 4.8923054658521945],
            },
            "mapPointEmpty": {
                "type": "Point",
                "coordinates": [52.379648, 4.9020928],
            },
            "mapPointHidden": {
                "type": "Point",
                "coordinates": [52.379648, 4.9020928],
            },
            "mapLineString": {
                "type": "LineString",
                "coordinates": [[4.893, 52.366], [4.894, 52.367], [4.895, 52.368]],
            },
            "mapLineStringEmpty": {
                "type": "LineString",
                "coordinates": [[4.893, 52.366], [4.894, 52.367], [4.895, 52.368]],
            },
            "mapLineStringHidden": {
                "type": "LineString",
                "coordinates": [[4.893, 52.366], [4.894, 52.367], [4.895, 52.368]],
            },
            "mapPolygon": {
                "type": "Polygon",
                "coordinates": [
                    [[4.893, 52.366], [4.893, 52.368], [4.895, 52.368], [4.895, 52.366]]
                ],
            },
            "mapPolygonEmpty": {
                "type": "Polygon",
                "coordinates": [
                    [[4.893, 52.366], [4.893, 52.368], [4.895, 52.368], [4.895, 52.366]]
                ],
            },
            "mapPolygonHidden": {
                "type": "Polygon",
                "coordinates": [
                    [[4.893, 52.366], [4.893, 52.368], [4.895, 52.368], [4.895, 52.366]]
                ],
            },
            "number": 1234,
            "numberEmpty": None,
            "numberHidden": 1234,
            "numberDecimal": 1234.56,
            "numberDecimalMulti": [1234.56, 100, 12.3, 1, 0],
            "numberMulti": [123123123, 123, 1, 0],
            "numberMultiEmpty": [None],
            "password": "secret",
            "passwordEmpty": "",
            "passwordHidden": "secret",
            "passwordMulti": ["secret", "password"],
            "passwordMultiEmpty": [None],
            "phoneNumber": "0123456789",
            "phoneNumberEmpty": "",
            "phoneNumberHidden": "0123456789",
            "phoneNumberMulti": ["0123456789", "0123456780"],
            "phoneNumberMultiEmpty": [None],
            "postcode": "1234 ab",
            "postcodeEmpty": "",
            "postcodeHidden": "1234 ab",
            "postcodeMulti": ["1234 ab", "4321 ba"],
            "postcodeMultiEmpty": [None],
            "radio": "aaa",
            "radioEmpty": "",
            "radioHidden": "aaa",
            "select": "aaa",
            "selectBoxes": ["aaa", "bbb"],
            "selectBoxesEmpty": [],
            "selectBoxesHidden": ["aaa"],
            "selectEmpty": "",
            "selectHidden": "aaa",
            "selectMulti": ["aaa", "bbb"],
            "selectMultiEmpty": [],
            # massive base64 blob, just read it from the JSON instead. This is unsure
            # yet how to handle anyway, as sending this much data into Camunda does not
            # seem a great idea.
            "signature": data["signature"],
            "signatureEmpty": "",
            "signatureHidden": "",
            "textArea": (
                "text with newline\ntext with blank line\n\ntext with newline\ntext "
                "with double blank line\n\n\ntext with newline\n"
            ),
            "textAreaEmpty": "",
            "textAreaHidden": "line 1\n\nline 2\n",
            "textAreaMulti": ["text no newline", "single line with newline\n"],
            "textAreaMultiEmpty": [""],
            "textField": "lower case text",
            "textFieldEmpty": "",
            "textFieldHidden": "lower case text",
            "textFieldMulti": ["lower case text", "Upper Case Text"],
            "textFieldMultiDefault": ["aaa", "bbb"],
            "textFieldMultiEmpty": [None],
            "time": time(12, 34),
            "timeEmpty": None,
            "timeHidden": time(12, 34),
            "timeMulti": [
                time(12, 34),
                time(21, 43),
            ],
            "timeMultiEmpty": [None],
        }

        for component in all_components:
            key = component["key"]
            if key in skip_keys:
                continue

            value = data.get(key, "NOT_IN_DATA")
            expected_python_value = expected.get(key, "NOT_EXPECTED")

            with self.subTest(
                component=component["key"], value=value, expected=expected_python_value
            ):
                result = to_python(component, value)

                self.assertEqual(result, expected_python_value)

    def test_all_types(self):
        all_components = load_json("all_components.json")["components"]
        data = load_json("all_components_data.json")
        expected = {
            "bsn": "123456782",
            "mapPoint": {
                "type": "Point",
                "coordinates": [52.3782943985417, 4.899629917973432],
            },
            "mapLineString": {
                "type": "LineString",
                "coordinates": [[4.893, 52.366], [4.894, 52.367], [4.895, 52.368]],
            },
            "mapPolygon": {
                "type": "Polygon",
                "coordinates": [
                    [[4.893, 52.366], [4.893, 52.368], [4.895, 52.368], [4.895, 52.366]]
                ],
            },
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
