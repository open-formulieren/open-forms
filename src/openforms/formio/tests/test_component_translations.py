"""
Test that component translations are respected in the context of a submission.
"""

from copy import deepcopy
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from hypothesis import given, strategies as st

from formio_types import (
    BSN,
    AddressNL,
    Checkbox,
    Content,
    CosignV1,
    CosignV2,
    Currency,
    Date,
    DateTime,
    EditGrid,
    Email,
    Fieldset,
    File,
    Iban,
    LicensePlate,
    Map,
    NpFamilyMembers,
    Number,
    Option,
    PhoneNumber,
    Postcode,
    Radio,
    Select,
    Selectboxes,
    Signature,
    Textarea,
    TextField,
    Time,
)
from formio_types._base import OptionExtensions, SupportedLanguage
from formio_types.address_nl import AddressNLExtensions, AddressNLTranslatableProperties
from formio_types.bsn import BSNExtensions, BSNTranslatableProperties
from formio_types.checkbox import CheckboxExtensions, CheckboxTranslatableProperties
from formio_types.content import ContentExtensions
from formio_types.cosign import (
    CosignV1Extensions,
    CosignV1TranslatableProperties,
    CosignV2Extensions,
    CosignV2TranslatableProperties,
)
from formio_types.currency import CurrencyExtensions, CurrencyTranslatableProperties
from formio_types.date import DateExtensions, DateTranslatableProperties
from formio_types.datetime import DateTimeExtensions, DateTimeTranslatableProperties
from formio_types.editgrid import (
    EditGridExtensions,
    EditGridTranslatableProperties,
    EditGridTranslations,
)
from formio_types.email import EmailExtensions, EmailTranslatableProperties
from formio_types.fieldset import FieldsetExtensions, FieldsetTranslatableProperties
from formio_types.file import FileExtensions, FileOptions, FileTranslatableProperties
from formio_types.iban import IbanExtensions, IbanTranslatableProperties
from formio_types.licenseplate import (
    LicensePlaceTranslatableProperties,
    LicensePlateExtensions,
)
from formio_types.map import MapExtensions, MapTranslatableProperties
from formio_types.np_family_members import (
    NpFamilyMembersExtensions,
    NpFamilyMembersTranslatableProperties,
)
from formio_types.number import NumberExtensions, NumberTranslatableProperties
from formio_types.phone_number import (
    PhoneNumberExtensions,
    PhoneNumberTranslatableProperties,
)
from formio_types.postcode import PostcodeExtensions, PostcodeTranslatableProperties
from formio_types.radio import RadioExtensions, RadioTranslatableProperties
from formio_types.select import SelectData
from formio_types.selectboxes import (
    SelectboxesExtensions,
    SelectboxesTranslatableProperties,
)
from formio_types.signature import SignatureExtensions, SignatureTranslatableProperties
from formio_types.textarea import TextareaExtensions, TextareaTranslatableProperties
from formio_types.textfield import TextFieldExtensions, TextFieldTranslatableProperties
from formio_types.time import TimeExtensions, TimeTranslatableProperties
from openforms.formio.typing.base import FormioConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.tests.search_strategies import language_code

from ..datastructures import FormioConfigurationWrapper
from ..formatters.tests.utils import load_json
from ..registry import register
from ..service import get_dynamic_configuration


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
            "label": "Repeating group",
            "groupLabel": "Item",
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
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

        configuration = get_dynamic_configuration(config_wrapper, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Text field")
            self.assertIsNone(textfield["openForms"]["translations"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Pick an option")
            self.assertIsNone(select["openForms"]["translations"])
            self.assertEqual(select["data"]["values"][0]["label"], "Option 1")
            self.assertIsNone(select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Option 2")
            self.assertIsNone(select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>EN content</p>")
            self.assertIsNone(content["openForms"]["translations"])

    def test_translations_applied_with_submission_language(self):
        form = FormFactory.build(translation_enabled=True)
        submission = SubmissionFactory.build(form=form, language_code="nl")
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

        configuration = get_dynamic_configuration(config_wrapper, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Tekstveld")
            self.assertIsNone(textfield["openForms"]["translations"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Maak een keuze")
            self.assertIsNone(select["openForms"]["translations"])
            self.assertEqual(select["data"]["values"][0]["label"], "Optie 1")
            self.assertIsNone(select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Optie 2")
            self.assertIsNone(select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>NL-inhoud</p>")
            self.assertIsNone(content["openForms"]["translations"])

    def test_translations_applied_with_fallback(self):
        form = FormFactory.build(translation_enabled=True)
        submission = SubmissionFactory.build(form=form, language_code="en")
        config_wrapper = FormioConfigurationWrapper(
            configuration=deepcopy(TEST_CONFIGURATION)
        )

        configuration = get_dynamic_configuration(config_wrapper, submission)

        with self.subTest("textfield"):
            textfield = configuration["textfield"]

            self.assertEqual(textfield["label"], "Text field")
            self.assertIsNone(textfield["openForms"]["translations"])

        with self.subTest("select"):
            select = configuration["select"]

            self.assertEqual(select["label"], "Pick an option")
            self.assertIsNone(select["openForms"]["translations"])
            self.assertEqual(select["data"]["values"][0]["label"], "Option 1")
            self.assertIsNone(select["data"]["values"][0]["openForms"])
            self.assertEqual(select["data"]["values"][1]["label"], "Option 2")
            self.assertIsNone(select["data"]["values"][1]["openForms"])

        with self.subTest("content (nested in editgrid)"):
            content = configuration["content"]

            self.assertEqual(content["html"], "<p>EN content</p>")
            self.assertIsNone(content["openForms"]["translations"])

    def test_does_not_crash_on_kitchensink(self):
        configuration: FormioConfiguration = load_json("kitchensink_components.json")
        config_wrapper = FormioConfigurationWrapper(configuration)

        with self.subTest(translation_enabled=True):
            form = FormFactory.build(translation_enabled=True)
            submission = SubmissionFactory.build(form=form, language_code="en")

            try:
                get_dynamic_configuration(config_wrapper, submission)
            except Exception as exc:
                raise self.failureException("Unexpected crash") from exc

        with self.subTest(translation_enabled=False):
            form = FormFactory.build(translation_enabled=False)
            submission = SubmissionFactory.build(form=form, language_code="en")

            try:
                get_dynamic_configuration(config_wrapper, submission)
            except Exception as exc:
                raise self.failureException("Unexpected crash") from exc


class ComponentTranslationTests(SimpleTestCase):
    """
    Test translations for a single component.
    """

    def test_generic_emptyish_translation(self):
        component = TextField(
            key="textfield",
            label="Label",
            description="Description",
            open_forms=TextFieldExtensions(
                translations={
                    "nl": {
                        "label": "",
                        # TODO: check if we have None-ish translations! Those should
                        # show up when parsing with msgspec though.
                        "description": "",
                    },
                }
            ),
        )

        register.localize_component(component, "nl", enabled=True)

        self.assertEqual(component.label, "Label")
        self.assertEqual(component.description, "Description")


class TextFieldTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_textfield(
        self,
        lang_code: SupportedLanguage,
        prop: TextFieldTranslatableProperties,
        translation: str,
    ):
        component = TextField(
            key="textfield",
            label="Must always have a label",
            open_forms=TextFieldExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class EmailTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_email(
        self,
        lang_code: SupportedLanguage,
        prop: EmailTranslatableProperties,
        translation: str,
    ):
        component = Email(
            key="email",
            label="Must always have a label",
            open_forms=EmailExtensions(
                translations={lang_code: {prop: translation}},
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class DateTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_date(
        self,
        lang_code: SupportedLanguage,
        prop: DateTranslatableProperties,
        translation: str,
    ):
        component = Date(
            key="date",
            label="Must always have a label",
            open_forms=DateExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class DateTetimeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_datetetime(
        self,
        lang_code: SupportedLanguage,
        prop: DateTimeTranslatableProperties,
        translation: str,
    ):
        component = DateTime(
            key="datetetime",
            label="Must always have a label",
            open_forms=DateTimeExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class TimeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_time(
        self,
        lang_code: SupportedLanguage,
        prop: TimeTranslatableProperties,
        translation: str,
    ):
        component = Time(
            key="time",
            label="Must always have a label",
            open_forms=TimeExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class PhoneTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_phone(
        self,
        lang_code: SupportedLanguage,
        prop: PhoneNumberTranslatableProperties,
        translation: str,
    ):
        component = PhoneNumber(
            key="phone",
            label="Must always have a label",
            open_forms=PhoneNumberExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class PostcodeTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_postcode(
        self,
        lang_code: SupportedLanguage,
        prop: PostcodeTranslatableProperties,
        translation: str,
    ):
        component = Postcode(
            key="postcode",
            label="Must always have a label",
            open_forms=PostcodeExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class FileTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_file(
        self,
        lang_code: SupportedLanguage,
        prop: FileTranslatableProperties,
        translation: str,
    ):
        component = File(
            key="file",
            label="Must always have a label",
            file=FileOptions(type=[]),
            file_pattern="",
            open_forms=FileExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class TextareaTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_textarea(
        self,
        lang_code: SupportedLanguage,
        prop: TextareaTranslatableProperties,
        translation: str,
    ):
        component = Textarea(
            key="textarea",
            label="Must always have a label",
            open_forms=TextareaExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class NumberTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_number(
        self,
        lang_code: SupportedLanguage,
        prop: NumberTranslatableProperties,
        translation: str,
    ):
        component = Number(
            key="number",
            label="Must always have a label",
            open_forms=NumberExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class CheckboxTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_checkbox(
        self,
        lang_code: SupportedLanguage,
        prop: CheckboxTranslatableProperties,
        translation: str,
    ):
        component = Checkbox(
            key="checkbox",
            label="Must always have a label",
            open_forms=CheckboxExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class SelectBoxesTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_selectboxes(
        self,
        lang_code: SupportedLanguage,
        prop: SelectboxesTranslatableProperties,
        translation: str,
    ):
        component = Selectboxes(
            key="selectboxes",
            label="Must always have a label",
            open_forms=SelectboxesExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code: SupportedLanguage, translation: str):
        component = Selectboxes(
            key="selectboxes",
            label="Must always have a label",
            values=[
                Option(
                    value="1",
                    label="First option",
                    open_forms=OptionExtensions(
                        translations={
                            lang_code: {
                                "label": translation,
                                "description": translation,
                            }
                        }
                    ),
                ),
            ],
        )

        register.localize_component(component, lang_code, enabled=True)

        assert component.values
        opt1 = component.values[0]

        self.assertEqual(opt1.label, translation)
        self.assertEqual(opt1.description, translation)
        self.assertIsNone(opt1.open_forms)


class SelectTranslationTests(SimpleTestCase):
    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code: SupportedLanguage, translation: str):
        component = Select(
            key="select",
            label="Must always have a label",
            data=SelectData(
                values=[
                    Option(
                        value="1",
                        label="First option",
                        open_forms=OptionExtensions(
                            translations={
                                lang_code: {
                                    "label": translation,
                                    "description": translation,
                                }
                            }
                        ),
                    ),
                ],
            ),
        )

        register.localize_component(component, lang_code, enabled=True)

        assert component.data.values
        opt1 = component.data.values[0]
        self.assertEqual(opt1.label, translation)
        self.assertEqual(opt1.description, translation)
        self.assertIsNone(opt1.open_forms)

    @given(lang_code=language_code)
    def test_no_options_present(self, lang_code: SupportedLanguage):
        # the data source can be set to a variable, for example
        component = Select(
            key="select",
            label="Must always have a label",
            data=SelectData(),
        )

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component.data.values, [])

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_option_not_translated_when_disabled(self, lang_code, translation):
        component = Select(
            key="select",
            label="Must always have a label",
            data=SelectData(
                values=[
                    Option(
                        value="1",
                        label="First option",
                        open_forms=OptionExtensions(
                            translations={
                                lang_code: {
                                    "label": translation,
                                    "description": translation,
                                }
                            }
                        ),
                    ),
                ],
            ),
        )

        register.localize_component(component, lang_code, enabled=False)

        assert component.data.values
        opt1 = component.data.values[0]
        self.assertEqual(opt1.label, "First option")
        self.assertIsNone(opt1.open_forms)

    @given(lang_code=language_code)
    def test_options_without_translations(self, lang_code):
        component = Select(
            key="select",
            label="Must always have a label",
            data=SelectData(
                values=[Option(value="1", label="First option")],
            ),
        )

        register.localize_component(component, lang_code, enabled=True)

        assert component.data.values
        opt1 = component.data.values[0]
        self.assertEqual(opt1.label, "First option")
        self.assertIsNone(opt1.open_forms)


class CurrencyTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_currency(
        self,
        lang_code: SupportedLanguage,
        prop: CurrencyTranslatableProperties,
        translation: str,
    ):
        component = Currency(
            key="currency",
            label="Must always have a label",
            open_forms=CurrencyExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class RadioTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_radio(
        self,
        lang_code: SupportedLanguage,
        prop: RadioTranslatableProperties,
        translation: str,
    ):
        component = Radio(
            key="radio",
            label="Must always have a label",
            open_forms=RadioExtensions(translations={lang_code: {prop: translation}}),
            values=[],
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)

    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_options_translated(self, lang_code: SupportedLanguage, translation: str):
        component = Radio(
            key="radio",
            label="Must always have a label",
            values=[
                Option(
                    value="1",
                    label="First option",
                    open_forms=OptionExtensions(
                        translations={
                            lang_code: {
                                "label": translation,
                                "description": translation,
                            }
                        }
                    ),
                ),
            ],
        )

        register.localize_component(component, lang_code, enabled=True)

        assert component.values
        opt1 = component.values[0]

        self.assertEqual(opt1.label, translation)
        self.assertEqual(opt1.description, translation)
        self.assertIsNone(opt1.open_forms)


class IBANTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_iban(
        self,
        lang_code: SupportedLanguage,
        prop: IbanTranslatableProperties,
        translation: str,
    ):
        component = Iban(
            key="iban",
            label="Must always have a label",
            open_forms=IbanExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class LicensePlateTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_licenseplate(
        self,
        lang_code: SupportedLanguage,
        prop: LicensePlaceTranslatableProperties,
        translation: str,
    ):
        component = LicensePlate(
            key="licenseplate",
            label="Must always have a label",
            open_forms=LicensePlateExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class BSNTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_bsn(
        self,
        lang_code: SupportedLanguage,
        prop: BSNTranslatableProperties,
        translation: str,
    ):
        component = BSN(
            key="bsn",
            label="Must always have a label",
            open_forms=BSNExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class NPFamilyMembersTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_npFamilyMembers(
        self,
        lang_code: SupportedLanguage,
        prop: NpFamilyMembersTranslatableProperties,
        translation: str,
    ):
        component = NpFamilyMembers(
            key="npFamilyMembers",
            label="Must always have a label",
            open_forms=NpFamilyMembersExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class SignatureTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_signature(
        self,
        lang_code: SupportedLanguage,
        prop: SignatureTranslatableProperties,
        translation: str,
    ):
        component = Signature(
            key="signature",
            label="Must always have a label",
            open_forms=SignatureExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class CoSignTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_cosign(
        self,
        lang_code: SupportedLanguage,
        prop: CosignV2TranslatableProperties,
        translation: str,
    ):
        component = CosignV2(
            key="cosign",
            label="Must always have a label",
            open_forms=CosignV2Extensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class OldCoSignTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_cosign_old(
        self,
        lang_code: SupportedLanguage,
        prop: CosignV1TranslatableProperties,
        translation: str,
    ):
        component = CosignV1(
            key="coSign",
            label="Must always have a label",
            open_forms=CosignV1Extensions(
                translations={lang_code: {prop: translation}}
            ),
            auth_plugin="digid",
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class MapTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_map(
        self,
        lang_code: SupportedLanguage,
        prop: MapTranslatableProperties,
        translation: str,
    ):
        component = Map(
            key="map",
            label="Must always have a label",
            open_forms=MapExtensions(translations={lang_code: {prop: translation}}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class ContentTranslationTests(SimpleTestCase):
    @given(lang_code=language_code, translation=st.text(min_size=1))
    def test_translatable_properties_content(
        self, lang_code: SupportedLanguage, translation: str
    ):
        component = Content(
            key="content",
            label="Must always have a label",
            html="Default value",
            open_forms=ContentExtensions(
                translations={lang_code: {"html": translation}}
            ),
        )

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(component.html, translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)


class FieldsetTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_fieldset(
        self,
        lang_code: SupportedLanguage,
        prop: FieldsetTranslatableProperties,
        translation: str,
    ):
        component = Fieldset(
            key="fieldset",
            label="Must always have a label",
            components=[
                TextField(
                    key="textfield",
                    label="Textfield",
                    open_forms=TextFieldExtensions(
                        translations={
                            lang_code: {
                                "label": "-translated-",
                            }
                        }
                    ),
                )
            ],
            open_forms=FieldsetExtensions(
                translations={lang_code: {prop: translation}}
            ),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)
        nested = component.components[0]
        assert isinstance(nested, TextField)
        self.assertEqual(nested.label, "Textfield")


class EditGridTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_editgrid(
        self,
        lang_code: SupportedLanguage,
        prop: EditGridTranslatableProperties,
        translation: str,
    ):
        translations = EditGridTranslations()
        setattr(translations, prop, translation)
        component = EditGrid(
            key="editgrid",
            label="Must always have a label",
            group_label="Item",
            components=[
                TextField(
                    key="textfield",
                    label="Textfield",
                    open_forms=TextFieldExtensions(
                        translations={lang_code: {"label": "-translated-"}}
                    ),
                )
            ],
            open_forms=EditGridExtensions(translations={lang_code: translations}),
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)
        nested = component.components[0]
        assert isinstance(nested, TextField)
        self.assertEqual(nested.label, "Textfield")


class AddressNLTranslationTests(SimpleTestCase):
    @given(
        lang_code=language_code,
        prop=...,
        translation=st.text(min_size=1),
    )
    def test_translatable_properties_adddressnl(
        self,
        lang_code: SupportedLanguage,
        prop: AddressNLTranslatableProperties,
        translation: str,
    ):
        component = AddressNL(
            key="addressNL",
            label="Must always have a label",
            open_forms=AddressNLExtensions(
                translations={lang_code: {prop: translation}}
            ),
            derive_address=False,
        )
        setattr(component, prop, f"Default {prop} value")

        register.localize_component(component, lang_code, enabled=True)

        self.assertEqual(getattr(component, prop), translation)
        assert component.open_forms is not None
        self.assertIsNone(component.open_forms.translations)
