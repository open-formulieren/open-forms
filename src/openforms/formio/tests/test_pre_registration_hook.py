from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import ComponentPreRegistrationResult, register
from ..typing.custom import DigitalAddress


class ProfilePreRegistrationHookTests(TestCase):
    def test_profile_has_hook(self):
        profile_component = {
            "key": "profile",
            "type": "customerProfile",
            "label": "Profile",
            "digitalAddressTypes": ["email", "phoneNumber"],
            "shouldUpdateCustomerData": True,
        }

        self.assertTrue(register.has_pre_registration_hook(profile_component))

    def test_profile_hook_should_update(self):
        profile_component = {
            "key": "profile",
            "type": "customerProfile",
            "label": "Profile",
            "digitalAddressTypes": ["phoneNumber", "email"],
            "shouldUpdateCustomerData": True,
        }
        profile_data: list[DigitalAddress] = [
            {"address": "some@email.com", "type": "email"},
            {"address": "0612345678", "type": "phoneNumber"},
        ]
        submission = SubmissionFactory.from_components(
            [profile_component],
            submitted_data={
                "profile": profile_data,
            },
        )

        result: ComponentPreRegistrationResult = register.apply_pre_registration_hook(
            profile_component, submission
        )

        self.assertEqual(result, {"data": None})

    def test_profile_hook_should_not_update(self):
        profile_component = {
            "key": "profile",
            "type": "customerProfile",
            "label": "Profile",
            "digitalAddressTypes": ["phoneNumber", "email"],
            "shouldUpdateCustomerData": False,
        }
        submission = SubmissionFactory.from_components([profile_component])

        result: ComponentPreRegistrationResult = register.apply_pre_registration_hook(
            profile_component, submission
        )

        self.assertEqual(result, {})


class TextFieldPreRegistrationHookTests(TestCase):
    def test_textfield_has_hook(self):
        text_component = {
            "key": "someText",
            "type": "textField",
            "label": "some text",
        }

        self.assertFalse(register.has_pre_registration_hook(text_component))

    def test_textfield_apply_hook(self):
        text_component = {
            "key": "someText",
            "type": "textField",
            "label": "some text",
        }
        submission = SubmissionFactory.from_components([text_component])

        with self.assertRaises(AssertionError):
            register.apply_pre_registration_hook(text_component, submission)
