from django.test import TestCase

from glom import glom
from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.formio.typing import AddressNLComponent
from openforms.submissions.tests.factories import SubmissionFactory

from ...datastructures import FormioConfigurationWrapper
from .. import get_translated_custom_error_messages


class ComponentWithCustomErrorsTests(ParametrizedTestCase, TestCase):
    def test_no_translated_errors(self):
        config = {
            "components": [
                {"key": "textField", "type": "textfield", "label": "Text Field"}
            ]
        }

        submission = SubmissionFactory.create(language_code="en")

        get_translated_custom_error_messages(
            FormioConfigurationWrapper(config), submission.language_code
        )

        self.assertNotIn("errors", config["components"][0])

    def test_custom_errors_in_english(self):
        config = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "label": "Text Field",
                    "translatedErrors": {
                        "en": {
                            "pattern": "{{ field }} has the wrong pattern!!!",
                            "required": "{{ field }} is required!!!",
                            "maxLength": "{{ field }} is too long!!!",
                        },
                        "nl": {
                            "pattern": "{{ field }} komt niet overeen met de regex!!!",
                            "required": "{{ field }} is verplicht!!!",
                            "maxLength": "{{ field }} is te lang!!!",
                        },
                    },
                }
            ]
        }

        submission = SubmissionFactory.create(language_code="en")

        get_translated_custom_error_messages(
            FormioConfigurationWrapper(config), submission.language_code
        )

        self.assertEqual(
            config["components"][0]["errors"],
            {
                "pattern": "{{ field }} has the wrong pattern!!!",
                "required": "{{ field }} is required!!!",
                "maxLength": "{{ field }} is too long!!!",
            },
        )

    def test_existing_errors_not_overwritten(self):
        config = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "label": "Text Field",
                    "translatedErrors": {
                        "en": {
                            "pattern": "{{ field }} has the wrong pattern!!!",
                            "required": "{{ field }} is required!!!",
                            "maxLength": "{{ field }} is too long!!!",
                        },
                        "nl": {
                            "pattern": "{{ field }} komt niet overeen met de regex!!!",
                            "required": "{{ field }} is verplicht!!!",
                            "maxLength": "{{ field }} is te lang!!!",
                        },
                    },
                    "errors": {"test": "test"},
                }
            ]
        }

        submission = SubmissionFactory.create(language_code="en")

        get_translated_custom_error_messages(
            FormioConfigurationWrapper(config), submission.language_code
        )

        self.assertEqual(
            config["components"][0]["errors"],
            {
                "test": "test",
            },
        )

    def test_addressnl_custom_error_messages(self):
        component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": {
                "components": {
                    "city": {
                        "validate": {"pattern": ""},
                        "translatedErrors": {
                            "en": {"pattern": "Custom city error"},
                            "nl": {"pattern": ""},
                        },
                    },
                    "postcode": {
                        "validate": {"pattern": ""},
                        "translatedErrors": {
                            "en": {"pattern": "Custom postcode error"},
                            "nl": {"pattern": ""},
                        },
                    },
                },
            },
        }

        get_translated_custom_error_messages(
            FormioConfigurationWrapper({"components": [component]}), "en"
        )

        assert "errors" in component["openForms"]["components"]["city"]
        self.assertEqual(
            component["openForms"]["components"]["city"]["errors"],
            {"pattern": "Custom city error"},
        )
        assert "errors" in component["openForms"]["components"]["postcode"]
        self.assertEqual(
            component["openForms"]["components"]["postcode"]["errors"],
            {"pattern": "Custom postcode error"},
        )

    def test_addressnl_custom_error_messages_noop(self):
        component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": {
                "components": {
                    "city": {
                        "validate": {"pattern": ""},
                        "errors": {"pattern": "no touch"},  # pyright: ignore[reportAssignmentType]
                        "translatedErrors": {
                            "en": {"pattern": "Custom city error"},
                            "nl": {"pattern": ""},
                        },
                    },
                },
            },
        }

        get_translated_custom_error_messages(
            FormioConfigurationWrapper({"components": [component]}), "en"
        )

        assert "openForms" in component
        assert "components" in component["openForms"]
        assert "city" in component["openForms"]["components"]
        assert "errors" in component["openForms"]["components"]["city"]
        self.assertEqual(
            component["openForms"]["components"]["city"]["errors"],
            {"pattern": "no touch"},
        )

    @parametrize(
        "extensions_config",
        [
            None,
            {"components": {}},
            {"components": {"postcode": {}}},
            {"components": {"postcode": {"validate": {"pattern": ""}}}},
            {"components": {"postcode": {"translatedErrors": {}}}},
            {"components": {"postcode": {"translatedErrors": {"en": {}}}}},
        ],
    )
    def test_addressnl_custom_error_messages_missing_config(self, extensions_config):
        component: AddressNLComponent = {
            "key": "addressNL",
            "type": "addressNL",
            "label": "Address",
            "deriveAddress": True,
            "openForms": extensions_config,
        }

        get_translated_custom_error_messages(
            FormioConfigurationWrapper({"components": [component]}), "en"
        )

        # assert that no translation is set
        sub_component = glom(component, "openForms.components.postcode", default={})
        self.assertNotIn("errors", sub_component)
