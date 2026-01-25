from django.test import TestCase

import msgspec

from formio_types import CustomerProfile, TextField
from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import ComponentPreRegistrationResult, register
from ..typing.custom import DigitalAddress


class ProfilePreRegistrationHookTests(TestCase):
    def test_profile_has_hook(self):
        self.assertTrue(register.has_pre_registration_hook("customerProfile"))

    def test_profile_hook_should_update(self):
        profile_component = CustomerProfile(
            key="profile",
            label="Profile",
            digital_address_types=["phoneNumber", "email"],
            should_update_customer_data=True,
        )
        profile_data: list[DigitalAddress] = [
            {"address": "some@email.com", "type": "email"},
            {"address": "0612345678", "type": "phoneNumber"},
        ]
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(profile_component)],
            submitted_data={
                "profile": profile_data,
            },
        )

        result: ComponentPreRegistrationResult = register.apply_pre_registration_hook(
            profile_component, submission
        )

        self.assertEqual(result, {"data": None})

    def test_profile_hook_should_not_update(self):
        profile_component = CustomerProfile(
            key="profile",
            label="Profile",
            digital_address_types=["phoneNumber", "email"],
            should_update_customer_data=False,
        )
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(profile_component)]
        )

        result: ComponentPreRegistrationResult = register.apply_pre_registration_hook(
            profile_component, submission
        )

        self.assertEqual(result, {})


class TextFieldPreRegistrationHookTests(TestCase):
    def test_textfield_has_hook(self):
        self.assertFalse(register.has_pre_registration_hook("textfield"))

    def test_textfield_apply_hook(self):
        text_component = TextField(
            key="someText",
            label="some text",
        )
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(text_component)]
        )

        with self.assertRaises(Exception) as exc:
            register.apply_pre_registration_hook(text_component, submission)
            self.assertIsInstance(exc.exception, AssertionError | KeyError)
