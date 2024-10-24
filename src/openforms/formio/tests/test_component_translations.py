"""
Test that component translations are respected in the context of a submission.
"""

from copy import deepcopy
from typing import Literal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from hypothesis import given, strategies as st
from rest_framework.test import APIRequestFactory

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.tests.search_strategies import language_code

from ..datastructures import FormioConfigurationWrapper
from ..formatters.tests.utils import load_json
from ..registry import register
from ..service import get_dynamic_configuration
from ..typing import RadioComponent, SelectComponent

rf = APIRequestFactory()


def disable_prefill_injection():
    """
    Disable prefill to prevent prefill-related queries.
    """
    return patch(
        "openforms.prefill.service.inject_prefill",
        new=MagicMock,
    )


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
class ConfigurationTranslationTests(SimpleTestCase):
    """
    Test some sample component types for translations at the component-level.

    This is not meant to exhaustively test all component types - for that, you should
    write appropriate unit tests for each supported component type. Rather, the
    mechanism here is tested to configure translations at the component level instead
    of at the form definition level. This avoids leaking excessive data to the
    frontend.

    Translations need to be 'injected' by the backend and be ready to use for the
    frontend, depending on the submission language.
    """

    def test_translations_ignored_if_form_disables_translations(self):
        form = FormFactory.build(translation_enabled=False)
        submission = SubmissionFactory.build(form=form)
        request = rf.get("/dummy")
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

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
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

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
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

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

    def test_does_not_crash_on_kitchensink(self):
        configuration = load_json("kitchensink_components.json")
        config_wrapper = FormioConfigurationWrapper(configuration)
        request = rf.get("/dummy")

        with self.subTest(translation_enabled=True):
            form = FormFactory.build(translation_enabled=True)
            submission = SubmissionFactory.build(form=form, language_code="en")

            try:
                get_dynamic_configuration(config_wrapper, request, submission)
            except Exception as exc:
                raise self.failureException("Unexpected crash") from exc

        with self.subTest(translation_enabled=False):
            form = FormFactory.build(translation_enabled=False)
            submission = SubmissionFactory.build(form=form, language_code="en")

            try:
                get_dynamic_configuration(config_wrapper, request, submission)
            except Exception as exc:
                raise self.failureException("Unexpected crash") from exc


class ComponentTranslationTests(SimpleTestCase):
    """
    Test translations for a single component.
    """

    def test_generic_emptyish_translation(self):
        component = {
            "type": "textfield",
            "key": "textfield",
            "label": "Label",
            "description": "Description",
            "openForms": {
                "translations": {
                    "nl": {
                        "label": "",
                        "description": None,
                    },
                }
            },
        }

        register.localize_component(component, "nl", enabled=True)

        self.assertEqual(component["label"], "Label")
        self.assertEqual(component["description"], "Description")


class TextFieldTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(
            ["label", "description", "tooltip", "defaultValue", "placeholder"]
        ),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_textfield(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "textfield",
            "key": "textfield",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class EmailTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_email(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "email",
            "key": "email",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class DateTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_date(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "date",
            "key": "date",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class DateTetimeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_datetetime(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "datetetime",
            "key": "datetetime",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class TimeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_time(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "time",
            "key": "time",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class PhoneTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_phone(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "phone",
            "key": "phone",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class PostcodeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_postcode(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "postcode",
            "key": "postcode",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class FileTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_file(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "file",
            "key": "file",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class TextareaTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(
            ["label", "description", "tooltip", "defaultValue", "placeholder"]
        ),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_textarea(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "textarea",
            "key": "textarea",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class NumberTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip", "suffix"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_number(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "number",
            "key": "number",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class CheckboxTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_checkbox(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "checkbox",
            "key": "checkbox",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class SelectBoxesTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_selectboxes(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "selectboxes",
            "key": "selectboxes",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code, translation):
        component = {
            "type": "selectboxes",
            "key": "selectboxes",
            "values": [
                {
                    "value": "1",
                    "label": "First option",
                    "openForms": {
                        "translations": {
                            lang_code: {
                                "label": translation,
                                "description": translation,
                            },
                        }
                    },
                }
            ],
        }

        register.localize_component(component, lang_code, enabled=True)

        assert "values" in component
        opt1 = component["values"][0]
        assert "label" in opt1
        assert "description" in opt1
        assert "openForms" in opt1

        self.assertEqual(opt1["label"], translation)
        self.assertEqual(opt1["description"], translation)
        self.assertNotIn("translations", opt1["openForms"])


class SelectTranslationTests(SimpleTestCase):
    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code, translation):
        component: SelectComponent = {
            "type": "select",
            "key": "select",
            "data": {
                "values": [
                    {
                        "value": "1",
                        "label": "First option",
                        "openForms": {
                            "translations": {
                                lang_code: {"label": translation},
                            }
                        },
                    }
                ],
            },
        }

        register.localize_component(component, lang_code, enabled=True)

        assert "values" in component["data"]
        opt1 = component["data"]["values"][0]
        assert "label" in opt1
        assert "openForms" in opt1
        self.assertEqual(opt1["label"], translation)
        self.assertNotIn("translations", opt1["openForms"])

    @given(lang_code=language_code)
    def test_no_options_present(self, lang_code):
        # the data source can be set to a variable, for example
        component: SelectComponent = {
            "type": "select",
            "key": "select",
            "data": {},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component["data"], {})

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_option_not_translated_when_disabled(self, lang_code, translation):
        component: SelectComponent = {
            "type": "select",
            "key": "select",
            "data": {
                "values": [
                    {
                        "value": "1",
                        "label": "First option",
                        "openForms": {
                            "translations": {
                                lang_code: {"label": translation},
                            }
                        },
                    }
                ],
            },
        }

        register.localize_component(component, lang_code, enabled=False)

        assert "values" in component["data"]
        opt1 = component["data"]["values"][0]
        assert "label" in opt1
        assert "openForms" in opt1
        self.assertEqual(opt1["label"], "First option")
        self.assertNotIn("translations", opt1["openForms"])

    @given(lang_code=language_code)
    def test_options_without_translations(self, lang_code):
        component: SelectComponent = {
            "type": "select",
            "key": "select",
            "data": {
                "values": [
                    {
                        "value": "1",
                        "label": "First option",
                    }
                ],
            },
        }

        register.localize_component(component, lang_code, enabled=True)

        assert "values" in component["data"]
        opt1 = component["data"]["values"][0]
        assert "label" in opt1
        self.assertEqual(opt1["label"], "First option")
        self.assertNotIn("openForms", opt1)


class CurrencyTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_currency(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "currency",
            "key": "currency",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class RadioTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_radio(
        self,
        lang_code: str,
        prop: Literal["label", "description", "tooltip"],
        translation: str,
    ):
        component: RadioComponent = {
            "type": "radio",
            "key": "radio",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
            "values": [],
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code, translation):
        component: RadioComponent = {
            "type": "radio",
            "key": "radio",
            "values": [
                {
                    "value": "1",
                    "label": "First option",
                    "openForms": {
                        "translations": {
                            lang_code: {
                                "label": translation,
                                "description": translation,
                            },
                        }
                    },
                }
            ],
        }

        register.localize_component(component, lang_code, enabled=True)

        assert "values" in component
        opt1 = component["values"][0]
        assert "label" in opt1
        assert "description" in opt1
        assert "openForms" in opt1
        self.assertEqual(opt1["label"], translation)
        self.assertEqual(opt1["description"], translation)
        self.assertNotIn("translations", opt1["openForms"])


class IBANTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_iban(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "iban",
            "key": "iban",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class LicensePlateTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_licenseplate(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "licenseplate",
            "key": "licenseplate",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class BSNTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_bsn(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "bsn",
            "key": "bsn",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class NPFamilyMembersTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_npFamilyMembers(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "npFamilyMembers",
            "key": "npFamilyMembers",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class SignatureTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_signature(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "signature",
            "key": "signature",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class CoSignTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_cosign(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "cosign",
            "key": "cosign",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class OldCoSignTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_cosign_old(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "coSign",
            "key": "coSign",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class MapTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_map(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "map",
            "key": "map",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])


class ContentTranslationTests(SimpleTestCase):
    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_translatable_properties_content(self, lang_code: str, translation: str):
        component = {
            "type": "content",
            "key": "content",
            "label": "Must always have a label",
            "html": "Default value",
            "openForms": {"translations": {lang_code: {"html": translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component["html"], translation)
        self.assertNotIn("translations", component["openForms"])


class FieldsetTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "tooltip"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_fieldset(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Textfield",
                    "openForms": {"translations": {lang_code: "-translated-"}},
                }
            ],
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])
        nested = component["components"][0]
        self.assertEqual(nested["label"], "Textfield")


class EditGridTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=st.sampled_from(["label", "description", "tooltip", "groupLabel"]),
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_editgrid(
        self, lang_code: str, prop: str, translation: str
    ):
        component = {
            "type": "editgrid",
            "key": "editgrid",
            "label": "Must always have a label",
            prop: f"Default {prop} value",
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Textfield",
                    "openForms": {"translations": {lang_code: "-translated-"}},
                }
            ],
            "openForms": {"translations": {lang_code: {prop: translation}}},
        }

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component[prop], translation)
        self.assertNotIn("translations", component["openForms"])
        nested = component["components"][0]
        self.assertEqual(nested["label"], "Textfield")
