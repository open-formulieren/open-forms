from django.test import SimpleTestCase, TestCase

from rest_framework import serializers

from openforms.submissions.tests.factories import (
    EmailVerificationFactory,
    SubmissionFactory,
)
from openforms.typing import JSONValue
from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class NoExampleComValidator(BasePlugin[str]):
    def __call__(self, value: str, submission):
        user, domain = value.rsplit("@", 1)
        if "example.com" == domain.lower():
            raise serializers.ValidationError("Nope")


class EmailValidationTests(SimpleTestCase):
    def test_email_required_validation(self):
        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "blank"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_email_pattern_validation(self):
        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
        }
        data: JSONValue = {"foo": "invalid-email"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_maxlength(self):
        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
            "validate": {"maxLength": 10},
        }
        data: JSONValue = {"foo": "foobar@example.com"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "max_length")

    def test_email_with_plugin_validator(self):
        with replace_validators_registry() as register:
            register("no_example_com")(NoExampleComValidator)

            component: Component = {
                "type": "email",
                "key": "foo",
                "label": "Test",
                "validate": {"plugins": ["no_example_com"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(
                    component, {"foo": "user@notexample.com"}
                )

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(
                    component, {"foo": "user@example.com"}
                )

                self.assertFalse(is_valid)


class EmailValidationDBTests(TestCase):
    def test_require_email_verification(self):
        submission = SubmissionFactory.create()
        # create some *unrelated* verification records
        ev = EmailVerificationFactory.create(
            component_key="foo", email="foobar@example.com", verified=True
        )
        assert ev.submission != submission
        EmailVerificationFactory(
            submission=submission,
            component_key="foo",
            email="foobar@example.com",
            verified=False,
        )
        EmailVerificationFactory(
            submission=submission,
            component_key="bar",
            email="foobar@example.com",
            verified=True,
        )
        EmailVerificationFactory(
            submission=submission,
            component_key="foo",
            email="other@example.com",
            verified=True,
        )

        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
            "openForms": {
                "requireVerification": True,
            },
        }
        data: JSONValue = {"foo": "foobar@example.com"}

        with self.subTest("not verified"):
            is_valid, errors = validate_formio_data(
                component, data, submission=submission
            )

            self.assertFalse(is_valid)
            error = extract_error(errors, "foo")
            self.assertEqual(error.code, "unverified")

        with self.subTest("verified"):
            # multiple successful verifications should not be a problem
            EmailVerificationFactory.create_batch(
                2,
                submission=submission,
                component_key="foo",
                email="foobar@example.com",
                verified=True,
            )

            is_valid, _ = validate_formio_data(component, data, submission=submission)

            self.assertTrue(is_valid)
