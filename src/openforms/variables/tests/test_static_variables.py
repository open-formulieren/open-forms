from datetime import datetime, timezone
from uuid import UUID

from django.test import TestCase, override_settings

from freezegun import freeze_time
from jsonschema import Draft202012Validator

from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import register_static_variable as register
from ..static_variables.static_variables import (
    CurrentYear,
    Environment,
    FormID,
    FormName,
    Now,
    Today,
)


def _get_variable(key: str, **kwargs):
    return register[key].get_static_variable(**kwargs)


@freeze_time("2022-08-29T17:10:55+02:00")
class NowTests(TestCase):
    def test_with_submission(self):
        submission = SubmissionFactory.build()

        variable = _get_variable("now", submission=submission)

        expected = datetime(2022, 8, 29, 15, 10, 0).replace(tzinfo=timezone.utc)
        self.assertEqual(variable.initial_value, expected)

    def test_without_submission(self):
        variable = _get_variable("now")

        expected = datetime(2022, 8, 29, 15, 10, 0).replace(tzinfo=timezone.utc)
        self.assertEqual(variable.initial_value, expected)


@freeze_time("2022-08-29T17:10:00+02:00")
class CurrentYearTests(TestCase):
    def test_with_submission(self):
        submission = SubmissionFactory.build()

        variable = _get_variable("current_year", submission=submission)

        self.assertEqual(variable.initial_value, 2022)

    def test_without_submission(self):
        variable = _get_variable("current_year")

        self.assertEqual(variable.initial_value, 2022)


class EnvironmentTests(TestCase):
    def test_with_submission(self):
        submission = SubmissionFactory.build()

        environments = (
            (None, "None"),
            ("", ""),
            ("production", "production"),
            ("other", "other"),
        )

        for env, expected in environments:
            with self.subTest(env=env, expected=expected):
                with override_settings(ENVIRONMENT=env):
                    variable = _get_variable("environment", submission=submission)

                    self.assertEqual(variable.initial_value, expected)

    def test_without_submission(self):
        environments = (
            (None, "None"),
            ("", ""),
            ("production", "production"),
            ("other", "other"),
        )

        for env, expected in environments:
            with self.subTest(env=env, expected=expected):
                with override_settings(ENVIRONMENT=env):
                    variable = _get_variable("environment")

                    self.assertEqual(variable.initial_value, expected)


class FormTests(TestCase):
    def test_without_submission(self):
        with self.subTest("form name"):
            variable = _get_variable("form_name")

            self.assertEqual(variable.initial_value, "")

        with self.subTest("form ID"):
            variable = _get_variable("form_id")

            self.assertEqual(variable.initial_value, "")

    def test_with_submission(self):
        submission = SubmissionFactory.create(
            form__name="Public form name",
            form__internal_name="Internal form name",
            form__uuid=UUID("f5ea7397-65c3-4ce0-b955-9b8f408e0ae0"),
        )

        with self.subTest("form name"):
            variable = _get_variable("form_name", submission=submission)

            self.assertEqual(variable.initial_value, "Public form name")

        with self.subTest("form ID"):
            variable = _get_variable("form_id", submission=submission)

            self.assertEqual(
                variable.initial_value, "f5ea7397-65c3-4ce0-b955-9b8f408e0ae0"
            )


class TodayTests(TestCase):
    @freeze_time("2022-11-24T00:30:00+01:00")
    def test_date_has_the_right_day(self):
        submission = SubmissionFactory.build()

        variable = _get_variable("today", submission=submission)

        self.assertEqual(variable.initial_value.day, 24)


class StaticVariablesValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def check_schema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.validator.check_schema(schema)

    def test_now(self):
        schema = Now.as_json_schema()
        self.check_schema(schema)

    def test_today(self):
        schema = Today.as_json_schema()
        self.check_schema(schema)

    def test_current_year(self):
        schema = CurrentYear.as_json_schema()
        self.check_schema(schema)

    def test_environment(self):
        schema = Environment.as_json_schema()
        self.check_schema(schema)

    def test_form_name(self):
        schema = FormName.as_json_schema()
        self.check_schema(schema)

    def test_form_id(self):
        schema = FormID.as_json_schema()
        self.check_schema(schema)
