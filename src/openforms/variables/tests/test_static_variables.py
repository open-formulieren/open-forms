from uuid import UUID

from django.test import TestCase, override_settings

from freezegun import freeze_time

from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import register_static_variable as register


def _get_variable(key: str, **kwargs):
    return register[key].get_static_variable(**kwargs)


@freeze_time("2022-08-29T17:10:00+02:00")
class NowTests(TestCase):
    def test_with_submission(self):
        submission = SubmissionFactory.build()

        variable = _get_variable("now", submission=submission)

        self.assertEqual(variable.initial_value, "2022-08-29T15:10:00+00:00")

    def test_without_submission(self):
        variable = _get_variable("now")

        self.assertEqual(variable.initial_value, "2022-08-29T15:10:00+00:00")


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
