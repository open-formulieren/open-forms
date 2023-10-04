"""
Test that component translations are respected in the context of a submission.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from rest_framework.test import APIRequestFactory

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..datastructures import FormioConfigurationWrapper
from ..service import get_dynamic_configuration

rf = APIRequestFactory()


def disable_prefill_injection():
    """
    Disable prefill to prevent prefill-related queries.
    """
    return patch("openforms.formio.service.inject_prefill", new=MagicMock)


TEST_CONFIGURATION = {
    "components": [
        {
            "type": "textfield",
            "key": "textfield",
            "label": "Text field",
            "openForms": {
                "translations": {
                    "nl": {
                        "label": "Tekstveld",
                    }
                }
            },
        },
        {
            "type": "select",
            "key": "select",
            "label": "Pick an option",
            "data": {
                "values": [
                    {
                        "value": "option1",
                        "label": "Option 1",
                        "openForms": {
                            "translations": {
                                "nl": {"label": "Optie 1"},
                            },
                        },
                    },
                    {
                        "value": "option2",
                        "label": "Option 2",
                        "openForms": {
                            "translations": {
                                "nl": {"label": "Optie 2"},
                            },
                        },
                    },
                ],
            },
            "openForms": {
                "translations": {
                    "nl": {
                        "label": "Maak een keuze",
                    }
                }
            },
        },
        {
            "type": "editgrid",
            "key": "editgrid",
            "components": [
                {
                    "type": "content",
                    "key": "content",
                    "html": "<p>EN content</p>",
                    "openForms": {
                        "translations": {
                            "nl": {
                                "html": "<p>NL-inhoud</p>",
                            }
                        }
                    },
                }
            ],
        },
    ],
}


@disable_prefill_injection()
class ComponentTranslationTests(SimpleTestCase):
    """
    Test some sample component types for translations at the component-level.

    This is not meant to exhaustively test all component types - for that, you should
    write appropriate unit tests for each supported component type. Rather, the
    mechanism here is tested to configure translations are the comopnent level instead
    of the entire form definition level and avoid leaking the excessive data to the
    frontend.

    Translations need to be 'injected' by the backend and be ready to use for the
    frontend, depending on the submission language.
    """

    def test_translations_ignored_if_form_disables_translations(self):
        form = FormFactory.build(translation_enabled=False)
        submission = SubmissionFactory.build(form=form)
        request = rf.get("/dummy")
        config_wrapper = FormioConfigurationWrapper(configuration=TEST_CONFIGURATION)

        configuration = get_dynamic_configuration(config_wrapper, request, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Text field")
            self.assertNotIn("translations", textfield["openForms"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Pick an option")
            self.assertNotIn("translations", select["openForms"])
            self.assertEqual(select["data"]["values"][0]["label"], "Option 1")
            self.assertNotIn("translations", select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Option 2")
            self.assertNotIn("translations", select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>EN content</p>")
            self.assertNotIn("translations", content["openForms"])

    def test_translations_applied_with_submission_language(self):
        form = FormFactory.build(translation_enabled=True)
        submission = SubmissionFactory.build(form=form, language_code="nl")
        request = rf.get("/dummy")
        config_wrapper = FormioConfigurationWrapper(configuration=TEST_CONFIGURATION)

        configuration = get_dynamic_configuration(config_wrapper, request, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Tekstveld")
            self.assertNotIn("translations", textfield["openForms"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Maak een keuze")
            self.assertNotIn("translations", select["openForms"])
            self.assertEqual(select["data"]["values"][0]["label"], "Optie 1")
            self.assertNotIn("translations", select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Optie 2")
            self.assertNotIn("translations", select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>NL-inhoud</p>")
            self.assertNotIn("translations", content["openForms"])

    def test_translations_applied_with_fallback(self):
        form = FormFactory.build(translation_enabled=True)
        submission = SubmissionFactory.build(form=form, language_code="en")
        request = rf.get("/dummy")
        config_wrapper = FormioConfigurationWrapper(configuration=TEST_CONFIGURATION)

        configuration = get_dynamic_configuration(config_wrapper, request, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Text field")
            self.assertNotIn("translations", textfield["openForms"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Pick an option")
            self.assertNotIn("translations", select["openForms"])
            self.assertEqual(select["data"]["values"][0]["label"], "Option 1")
            self.assertNotIn("translations", select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Option 2")
            self.assertNotIn("translations", select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>EN content</p>")
            self.assertNotIn("translations", content["openForms"])
