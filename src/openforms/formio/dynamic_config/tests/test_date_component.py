from copy import deepcopy
from datetime import datetime
from typing import Any

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time
from rest_framework.test import APIRequestFactory

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.service import get_static_variables

from ...service import FormioConfigurationWrapper, get_dynamic_configuration
from ...typing import DateComponent

request_factory = APIRequestFactory()


class DynamicDateConfigurationTests(TestCase):
    @staticmethod
    def _get_dynamic_config(
        component: DateComponent, variables: dict[str, Any]
    ) -> DateComponent:
        config_wrapper = FormioConfigurationWrapper({"components": [component]})
        request = request_factory.get("/irrelevant")
        submission = SubmissionFactory.create()
        static_vars = get_static_variables(submission=submission)  # don't do queries
        variables.update({var.key: var.initial_value for var in static_vars})
        config_wrapper = get_dynamic_configuration(
            config_wrapper, request=request, submission=submission, data=variables
        )
        new_configuration = config_wrapper.configuration
        return new_configuration["components"][0]

    def test_legacy_configuration_still_works(self):
        # legacy configuration = without the openForms.minDate keys etc.
        component = {
            "type": "date",
            "key": "aDate",
            "datePicker": {
                "minDate": None,
                "maxDate": "2022-09-08T00:00:00+02:00",
            },
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertIsNone(new_component["datePicker"]["minDate"])
        self.assertEqual(
            new_component["datePicker"]["maxDate"], "2022-09-08T00:00:00+02:00"
        )

    def test_min_max_date_fixed_value(self):
        component = {
            "type": "date",
            "key": "aDate",
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

        self.assertIsNone(new_component["datePicker"]["minDate"])
        self.assertEqual(
            new_component["datePicker"]["maxDate"], "2022-09-08T00:00:00+02:00"
        )

    @freeze_time("2022-09-12T14:07:00Z")
    def test_min_date_future(self):
        date_component = {
            "type": "date",
            "key": "aDate",
            "openForms": {"minDate": {"mode": "future"}},
            "datePicker": {"minDate": None},
        }

        with self.subTest(include_today=True):
            component = deepcopy(date_component)
            component["openForms"]["minDate"]["includeToday"] = True

            new_component = self._get_dynamic_config(component, {})

            self.assertEqual(
                new_component["datePicker"]["minDate"], "2022-09-12T00:00:00+02:00"
            )

        with self.subTest(include_today=False):
            component = deepcopy(date_component)
            component["openForms"]["minDate"]["includeToday"] = False

            new_component = self._get_dynamic_config(component, {})

            self.assertEqual(
                new_component["datePicker"]["minDate"],
                "2022-09-13T00:00:00+02:00",
            )

    @freeze_time("2022-09-12T14:07:00Z")
    def test_max_date_past(self):
        date_component = {
            "type": "date",
            "key": "aDate",
            "openForms": {"maxDate": {"mode": "past"}},
            "datePicker": {"maxDate": None},
        }

        with self.subTest(include_today=True):
            component = deepcopy(date_component)
            component["openForms"]["maxDate"]["includeToday"] = True

            new_component = self._get_dynamic_config(component, {})

            self.assertEqual(
                new_component["datePicker"]["maxDate"],
                "2022-09-12T00:00:00+02:00",
            )

        with self.subTest(include_today=False):
            component = deepcopy(date_component)
            component["openForms"]["maxDate"]["includeToday"] = False

            new_component = self._get_dynamic_config(component, {})

            self.assertEqual(
                new_component["datePicker"]["maxDate"],
                "2022-09-11T00:00:00+02:00",
            )

    @freeze_time("2022-10-03T12:00:00Z")
    def test_relative_to_variable_blank_delta(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "operator": "",
                    "delta": {
                        "days": None,
                        "months": None,
                        # "years": None,  omitted deliberately - backend must handle missing keys
                    },
                },
            },
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertEqual(
            new_component["datePicker"]["minDate"], "2022-10-03T00:00:00+02:00"
        )

    @freeze_time("2022-11-03T12:00:00Z")
    def test_relative_to_variable_blank_delta_dst_over(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "operator": "",
                    "delta": {
                        "days": None,
                        "months": None,
                        # "years": None,  omitted deliberately - backend must handle missing keys
                    },
                },
            },
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertEqual(
            new_component["datePicker"]["minDate"], "2022-11-03T00:00:00+01:00"
        )

    def test_relative_to_variable_add_delta(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "minDate": {
                    "mode": "relativeToVariable",
                    "variable": "someDate",
                    "operator": "add",
                    "delta": {
                        "days": 21,
                        "months": None,
                    },
                },
            },
        }
        # Amsterdam time
        some_date = timezone.make_aware(datetime(2022, 10, 14, 0, 0, 0))
        assert some_date.tzinfo.key == "Europe/Amsterdam"

        new_component = self._get_dynamic_config(component, {"someDate": some_date})

        self.assertEqual(
            new_component["datePicker"]["minDate"],
            "2022-11-04T00:00:00+01:00",  # Nov. 4th Amsterdam time, where DST has ended
        )

    def test_relative_to_variable_subtract_delta(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "someDate",
                    "operator": "subtract",
                    "delta": {
                        "months": 1,
                    },
                },
            },
        }
        # Amsterdam time
        some_date = timezone.make_aware(datetime(2022, 10, 14, 0, 0, 0))
        assert some_date.tzinfo.key == "Europe/Amsterdam"

        new_component = self._get_dynamic_config(component, {"someDate": some_date})

        self.assertEqual(
            new_component["datePicker"]["maxDate"], "2022-09-14T00:00:00+02:00"
        )

    def test_variable_empty_or_none(self):
        component = {
            "type": "date",
            "key": "aDate",
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

                self.assertIsNone(new_component["datePicker"]["maxDate"])

    @tag("gh-2581")
    def test_variable_is_string_serialized_date(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "stringVar",
                    "operator": "add",
                },
            },
        }

        values = ["2023-01-30", "2023-01-30T15:22:00+01:00"]
        for value in values:
            with self.subTest(value=value):
                new_component = self._get_dynamic_config(
                    component, {"stringVar": value}
                )

                max_date = new_component["datePicker"]["maxDate"]
                self.assertEqual(max_date, "2023-01-30T00:00:00+01:00")

    @tag("gh-2581")
    def test_nonsense_variable(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {
                "maxDate": {
                    "mode": "relativeToVariable",
                    "variable": "emptyVar",
                    "operator": "add",
                },
            },
        }

        # Discussed in office - essentially we have two options:
        # * crashing hard
        # * silently casting to None, removing any expected constraints from the
        #   date picker, possibly allowing garbage into registration backends that was
        #   not anticipated
        #
        # We picked option 1, as the end-user will receive a generic error message from
        # the SDK, so they can contact their municipality, who in turn contact the service
        # provider, who in turn can look up the crash/error in Sentry and provide the
        # fixes.
        #
        # Option 2 is harder to debug without visbility in error monitoring and therefore
        # not desired.
        with self.assertRaises(ValueError):
            self._get_dynamic_config(component, {"emptyVar": "foobar"})

    @tag("gh-2581")
    def test_incomplete_config_no_crash(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {"maxDate": {}},
            "datePicker": {"maxDate": "2022-09-12T14:08:00Z"},
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertEqual(new_component["datePicker"]["maxDate"], "2022-09-12T14:08:00Z")

    @tag("gh-2525")
    def test_configuration_after_delete_validation(self):
        component = {
            "type": "date",
            "key": "aDate",
            # This is the configuration that gets saved if the maxDate validation is removed in the editForm
            "openForms": {"maxDate": {"mode": ""}},
            "datePicker": {"maxDate": None},
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertIsNone(new_component["datePicker"]["maxDate"])
