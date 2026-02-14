from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ...datastructures import FormioConfigurationWrapper
from .. import get_translated_custom_error_messages


class ComponentWithCustomErrorsTests(TestCase):
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
