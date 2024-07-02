from django.test import SimpleTestCase, tag
from django.utils import timezone

from openforms.submissions.models import Submission
from openforms.utils.date import get_today

from ...datastructures import FormioConfigurationWrapper
from ...dynamic_config import rewrite_formio_components
from ...typing import DateComponent
from .helpers import extract_error, validate_formio_data


class DateFieldValidationTests(SimpleTestCase):

    def test_datefield_required_validation(self):
        component: DateComponent = {
            "type": "date",
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

    def test_min_max_date(self):
        component: DateComponent = {
            "type": "date",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
            "datePicker": {
                "minDate": "2024-03-10",
                "maxDate": "2025-03-10",
            },
        }

        invalid_values = [
            ({"foo": "2023-01-01"}, "min_value"),
            ({"foo": "2025-12-30"}, "max_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    @tag("gh-4172")
    def test_min_max_can_be_datetimes(self):
        # Our dynamic logic that calculates dates/datetimes is shared between date
        # and datetime components, so it produces datetime strings (!)
        component: DateComponent = {
            "type": "date",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
            "openForms": {
                "minDate": {
                    "mode": "future",
                    "includeToday": True,
                },
            },
        }
        submission = Submission()  # this test is not supposed to hit the DB
        config_wraper = FormioConfigurationWrapper(
            configuration={"components": [component]}
        )
        config_wraper = rewrite_formio_components(
            config_wraper,
            submission=submission,
            data={"now": timezone.now()},
        )

        updated_component = config_wraper["foo"]
        # check that rewrite_formio_components behaved as expected
        assert "datePicker" in updated_component
        assert "minDate" in updated_component["datePicker"]

        with self.subTest("valid value"):
            # use localized date in Amsterdam, otherwise the test fails between midnight
            # and 1am/2am depending on DST
            today = get_today()
            is_valid, _ = validate_formio_data(component, {"foo": today})

            self.assertTrue(is_valid)

        with self.subTest("invalid value"):
            is_valid, _ = validate_formio_data(component, {"foo": "2020-01-01"})

            self.assertFalse(is_valid)

    @tag("gh-4068")
    def test_empty_default_value(self):
        component: DateComponent = {
            "type": "date",
            "key": "date",
            "label": "Optional date",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"date": ""})

        self.assertTrue(is_valid)
