from django.test import TestCase, tag
from django.utils.translation import gettext_lazy as _

from openforms.submissions.tests.factories import SubmissionFactory

from ...typing.custom import CustomerProfileComponent
from .helpers import extract_error, validate_formio_data


@tag("gh-6155")
class ProfileValidationTests(TestCase):
    def test_validate_profile_not_empty_valid(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email", "phoneNumber"],
            "shouldUpdateCustomerData": True,
            "validate": {
                "required": True,
            },
        }

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        valid_values = {
            "profile": [
                {
                    "address": "john@smith.org",
                    "type": "email",
                },
                {
                    "address": "0612345678",
                    "type": "phoneNumber",
                },
            ]
        }

        is_valid, _ = validate_formio_data(component, valid_values, submission)

        self.assertTrue(is_valid)

    def test_validate_profile_empty_valid(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email", "phoneNumber"],
            "shouldUpdateCustomerData": True,
            "validate": {},
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        valid_values = {
            "profile": [
                {
                    "address": "",
                    "type": "email",
                    "preferenceUpdate": "useOnlyOnce",
                },
                {
                    "address": "",
                    "type": "phoneNumber",
                    "preferenceUpdate": "useOnlyOnce",
                },
            ]
        }
        is_valid, _ = validate_formio_data(component, valid_values, submission)

        self.assertTrue(is_valid)

    def test_validate_profile_wrong_data_format(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email", "phoneNumber"],
            "shouldUpdateCustomerData": True,
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        values = {"profile": "This data makes no sense"}

        is_valid, _ = validate_formio_data(component, values, submission)

        self.assertFalse(is_valid)

    def test_validate_address_type_not_included_into_config(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email"],
            "shouldUpdateCustomerData": True,
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        values = {
            "profile": [
                {
                    "address": "john@smith.org",
                    "type": "email",
                    "preferenceUpdate": "useOnlyOnce",
                },
                {
                    "address": "0812345678",
                    "type": "phoneNumber",
                    "preferenceUpdate": "useOnlyOnce",
                },
            ]
        }

        is_valid, errors = validate_formio_data(component, values, submission)

        type_error = extract_error(errors["profile"][1], "type")

        self.assertFalse(is_valid)
        self.assertEqual(type_error.code, "invalid_choice")

    def test_validate_profile_wrong_address_format_email(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email"],
            "shouldUpdateCustomerData": True,
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    component,
                ]
            },
        )
        values = {
            "profile": [
                {
                    "address": "some-incorrect-email",
                    "type": "email",
                },
            ]
        }

        is_valid, errors = validate_formio_data(component, values, submission)

        error = extract_error(errors["profile"][0], "non_field_errors")

        self.assertFalse(is_valid)
        self.assertEqual(error, _("Enter a valid email address."))

    def test_validate_profile_wrong_address_format_phone_number(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["phoneNumber"],
            "shouldUpdateCustomerData": True,
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    component,
                ]
            },
        )
        values = {
            "profile": [
                {
                    "address": "0ABC",
                    "type": "phoneNumber",
                },
            ]
        }
        is_valid, errors = validate_formio_data(component, values, submission)

        error = extract_error(errors["profile"][0], "non_field_errors")

        self.assertFalse(is_valid)
        self.assertEqual(error, _("Enter a valid phone number."))

    def test_validate_profile_duplicated_types(self):
        component: CustomerProfileComponent = {
            "key": "profile",
            "label": "profile",
            "type": "customerProfile",
            "digitalAddressTypes": ["email", "phoneNumber"],
            "shouldUpdateCustomerData": True,
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    component,
                ]
            },
        )
        values = {
            "profile": [
                {
                    "address": "john@smith.org",
                    "type": "email",
                },
                {
                    "address": "another@email.org",
                    "type": "email",
                },
                {
                    "address": "0812345678",
                    "type": "phoneNumber",
                },
            ]
        }

        is_valid, errors = validate_formio_data(component, values, submission)
        error = extract_error(errors["profile"], "non_field_errors")

        self.assertFalse(is_valid)
        self.assertEqual(
            error,
            _(
                "You cannot submit multiple digital addresses for the type '{type}'."
            ).format(type="email"),
        )
