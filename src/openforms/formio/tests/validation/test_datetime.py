from django.test import SimpleTestCase
from django.utils import timezone

from openforms.submissions.models import Submission
from openforms.typing import JSONValue

from ...datastructures import FormioConfigurationWrapper, FormioData
from ...dynamic_config import rewrite_formio_components
from ...typing import DatetimeComponent
from .helpers import extract_error, validate_formio_data


class DatetimeFieldValidationTests(SimpleTestCase):
    def test_datetimefield_required_validation(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
            ({"foo": ""}, "required"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_min_max_datetime(self):
        # variant with explicit fixed values
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
            "openForms": {
                "minDate": {"mode": "fixedValue"},
                "maxDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "minDate": "2024-03-10T12:00",
                "maxDate": "2025-03-10T22:30",
            },
        }

        invalid_values = [
            ({"foo": "2023-01-01T12:00:00+00:00"}, "min_value"),
            ({"foo": "2025-05-17T12:00:00+02:00"}, "max_value"),
            ({"foo": "2024-05-17"}, "invalid"),
            ({"foo": "blah"}, "invalid"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

        valid_values = [
            "2024-05-06T13:49:00+02:00",
            "2024-03-10T12:00:00+01:00",  # exactly on the minimum value, without DST
            "2025-03-10T22:30:00+01:00",  # exactly on the maximum value, without DST
        ]
        for value in valid_values:
            with self.subTest("valid value", value=value):
                is_valid, _ = validate_formio_data(component, {"foo": value})

                self.assertTrue(is_valid)

    def test_dynamic_configuration(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
            "openForms": {
                "minDate": {
                    "mode": "future",
                },
            },
        }
        submission = Submission()  # this test is not supposed to hit the DB
        config_wraper = FormioConfigurationWrapper(
            configuration={"components": [component]}
        )
        now = timezone.now()
        config_wraper = rewrite_formio_components(
            config_wraper,
            submission=submission,
            data=FormioData({"now": now}),
        )

        updated_component = config_wraper["foo"]
        # check that rewrite_formio_components behaved as expected
        assert "datePicker" in updated_component
        assert "minDate" in updated_component["datePicker"]

        with self.subTest("valid value"):
            is_valid, _ = validate_formio_data(component, {"foo": now.isoformat()})

            self.assertTrue(is_valid)

        with self.subTest("invalid value"):
            is_valid, _ = validate_formio_data(
                component, {"foo": "2020-01-01T12:00:00+01:00"}
            )

            self.assertFalse(is_valid)

    def test_empty_default_value(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "datetime",
            "label": "Optional datetime",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"datetime": ""})

        self.assertTrue(is_valid)

    def test_multiple(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "datetimes",
            "label": "Multiple datetimes",
            "multiple": True,
            "defaultValue": [],
        }
        data: JSONValue = {"datetimes": ["2024-01-01T00:00:00+00:00", "notdatetime"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = errors["datetimes"][1][0]
        self.assertEqual(error.code, "invalid")

        with self.subTest("valid item"):
            self.assertNotIn(0, errors["datetimes"])
