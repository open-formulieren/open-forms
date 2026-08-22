import zoneinfo
from datetime import datetime

from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from formio_types import DateTime
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import VariableValue
from openforms.variables.service import get_static_variables

from ...service import FormioConfig, FormioData, get_dynamic_configuration
from ...typing import DatetimeComponent


@override_settings(TIME_ZONE="Europe/Amsterdam")
class DynamicDatetimeConfigurationTests(TestCase):
    @staticmethod
    def _get_dynamic_config(
        component: DatetimeComponent, variables: dict[str, VariableValue]
    ) -> DateTime:
        formio_config = FormioConfig(name="<test>", components=[component])
        submission = SubmissionFactory.create()
        static_vars = get_static_variables(submission=submission)  # don't do queries
        variables.update({var.key: var.initial_value for var in static_vars})
        formio_config = get_dynamic_configuration(
            formio_config, submission=submission, data=FormioData(variables)
        )
        _updated_component = formio_config[component["key"]]
        assert isinstance(_updated_component, DateTime)
        return _updated_component

    def test_validation_fixed_value_legacy_configuration(self):
        # legacy configuration = without the openForms.minDate keys etc.
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "datePicker": {
                "minDate": None,
                "maxDate": "2022-09-08T00:00:00+02:00",
            },
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertIsNone(new_component.date_picker.min_date)
        self.assertEqual(
            new_component.date_picker.max_date, "2022-09-08T00:00:00+02:00"
        )

    def test_min_max_datetime_fixed_value(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "minDate": {"mode": "fixedValue"},
                "maxDate": {"mode": "fixedValue"},
            },
            "datePicker": {
                "minDate": None,
                "maxDate": "2022-09-08T00:00:00+02:00",
            },
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertIsNone(new_component.date_picker.min_date)
        self.assertEqual(
            new_component.date_picker.max_date, "2022-09-08T00:00:00+02:00"
        )

    @freeze_time("2022-09-12T14:07:00Z")
    def test_min_datetime_future(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {"minDate": {"mode": "future"}},
            "datePicker": {"minDate": None, "maxDate": None},
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertEqual(
            new_component.date_picker.min_date, "2022-09-12T16:07:00+02:00"
        )

    @freeze_time("2022-09-12T14:07:00Z")
    def test_max_datetime_past(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {"maxDate": {"mode": "past"}},
            "datePicker": {"minDate": None, "maxDate": None},
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertEqual(
            new_component.date_picker.max_date,
            "2022-09-12T16:07:00+02:00",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_datetime_placeholder(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertEqual(new_component.placeholder, "dd-mm-yyyy HH:mm")

    @freeze_time("2022-10-03T12:00:00Z")
    def test_relative_to_variable_blank_delta(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "delta": {
                        "days": None,
                        "months": None,
                        # "years": None,  omitted deliberately - backend must handle missing keys
                    },
                },
            },
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertEqual(
            new_component.date_picker.min_date, "2022-10-03T14:00:00+02:00"
        )

    @freeze_time("2022-11-03T12:00:00Z")
    def test_relative_to_variable_blank_delta_dst_over(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "delta": {
                        "days": None,
                        "months": None,
                        # "years": None,  omitted deliberately - backend must handle missing keys
                    },
                },
            },
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertEqual(
            new_component.date_picker.min_date, "2022-11-03T13:00:00+01:00"
        )

    def test_relative_to_variable_add_delta(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "someDatetime",
                    "operator": "add",
                    "delta": {
                        "days": 21,
                        "months": None,
                    },
                },
            },
        }
        # Amsterdam time
        some_date = timezone.make_aware(datetime(2022, 10, 14, 15, 0, 0))
        assert isinstance(some_date.tzinfo, zoneinfo.ZoneInfo)
        assert some_date.tzinfo.key == "Europe/Amsterdam"

        new_component = self._get_dynamic_config(component, {"someDatetime": some_date})

        assert new_component.date_picker is not None
        # DST ended on Oct 30, so we go from UTC+2 to UTC+1 (clock goes backwards one hour)
        # On Django 3.2, this hour backwards was calculated in, but on 4.2 the local time
        # (15:00) stays identical. You can argue for both of those cases that they're the
        # correct behaviour...
        # At least the zoneinfo variant ends up with the correct final timezone...
        self.assertEqual(
            new_component.date_picker.min_date,
            "2022-11-04T15:00:00+01:00",  # Nov. 4th Amsterdam time, where DST has ended
        )

    def test_relative_to_variable_subtract_delta(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "someDatetime",
                    "operator": "subtract",
                    "delta": {
                        "months": 1,
                    },
                },
            },
        }
        # Amsterdam time
        some_date = timezone.make_aware(datetime(2022, 10, 14, 15, 0, 0))
        assert some_date.tzinfo.key == "Europe/Amsterdam"

        new_component = self._get_dynamic_config(component, {"someDatetime": some_date})

        self.assertEqual(
            new_component.date_picker.max_date, "2022-09-14T15:00:00+02:00"
        )

    def test_variable_empty_or_none(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "emptyVar",
                    "operator": "add",
                },
            },
        }
        empty_values = [None, ""]

        for empty_value in empty_values:
            with self.subTest(empty_value=empty_value):
                new_component = self._get_dynamic_config(
                    component, {"emptyVar": empty_value}
                )

                assert new_component.date_picker is not None
                self.assertIsNone(new_component.date_picker.max_date)

    @freeze_time("2022-11-03T12:00:05.12345Z")
    def test_seconds_microseconds_are_truncated(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "operator": "add",
                    "delta": {
                        "days": 0,
                        "months": 0,
                        "years": 0,
                    },
                },
            },
        }

        new_component = self._get_dynamic_config(component, {})

        assert new_component.date_picker is not None
        self.assertEqual(
            new_component.date_picker.min_date, "2022-11-03T13:00:00+01:00"
        )

    def test_variable_of_wrong_type_string(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "wrongVar",
                    "operator": "add",
                },
            },
        }

        with self.assertRaises(TypeError):
            self._get_dynamic_config(component, {"wrongVar": "Im not a datetime!! :("})

    def test_variable_string_datetime(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "stringDateVar",
                    "operator": "add",
                    "delta": {
                        "days": 0,
                        "months": 0,
                        "years": 0,
                    },
                },
            },
        }

        # With the work done in #2324, we expect data returned from the state to
        # already be in date/datetime objects, so this is not allowed anymore
        with self.assertRaises(TypeError):
            self._get_dynamic_config(
                component, {"stringDateVar": "2023-01-30T15:22:00+01:00"}
            )

    def test_variable_of_wrong_type_list(self):
        component: DatetimeComponent = {
            "type": "datetime",
            "key": "aDatetime",
            "label": "Datetime",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "wrongVar",
                    "operator": "add",
                },
            },
        }

        with self.assertRaises(TypeError):
            self._get_dynamic_config(
                component, {"wrongVar": ["Im not a datetime!! :("]}
            )
