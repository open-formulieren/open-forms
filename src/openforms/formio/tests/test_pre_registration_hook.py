from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import register
from ..typing.base import ComponentPreRegistrationResult


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
        submission = SubmissionFactory.from_components([profile_component])

        with patch(
            "openforms.contrib.customer_interactions.utils.update_customer_interaction_data",
            lambda submission, profile_key: "something",
        ):
            result: ComponentPreRegistrationResult = (
                register.apply_pre_registration_hook(profile_component, submission)
            )

        self.assertEqual(result, {"data": "something"})

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

        result: ComponentPreRegistrationResult = register.apply_pre_registration_hook(
            text_component, submission
        )

        self.assertIsNone(result)
