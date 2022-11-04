from copy import deepcopy
from datetime import datetime
from typing import Any, Dict

from django.test import SimpleTestCase
from django.utils import timezone

from freezegun import freeze_time
from rest_framework.test import APIRequestFactory

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.service import get_static_variables

from ...dynamic_config.date import FormioDateComponent
from ...service import FormioConfigurationWrapper, get_dynamic_configuration
from ...typing import Component

request_factory = APIRequestFactory()


class DynamicDateConfigurationTests(SimpleTestCase):
    @staticmethod
    def _get_dynamic_config(
        component: Component, variables: Dict[str, Any]
    ) -> FormioDateComponent:
        config_wrapper = FormioConfigurationWrapper({"components": [component]})
        request = request_factory.get("/irrelevant")
        submission = SubmissionFactory.build()
        static_vars = get_static_variables(submission=None)  # don't do queries
        variables.update({var.key: var.to_python() for var in static_vars})
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
        assert some_date.tzinfo.zone == "Europe/Amsterdam"

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
        assert some_date.tzinfo.zone == "Europe/Amsterdam"

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

        new_component = self._get_dynamic_config(component, {"emptyVar": None})

        self.assertIsNone(new_component["datePicker"]["maxDate"])

    def test_incomplete_config_no_crash(self):
        component = {
            "type": "date",
            "key": "aDate",
            "openForms": {"maxDate": {}},
            "datePicker": {"maxDate": "2022-09-12T14:08:00Z"},
        }

        new_component = self._get_dynamic_config(component, {})

        self.assertEqual(new_component["datePicker"]["maxDate"], "2022-09-12T14:08:00Z")
