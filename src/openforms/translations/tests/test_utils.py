from django.conf import settings
from django.test import TestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory

from ..utils import to_iso639_2b
from .utils import make_translated


class MakeTranslatedFactoryTests(TestCase):
    def test_sets_values_for_passed_args(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(_language="en", name="my name")

        self.assertEqual(form.name_en, "my name")
        self.assertFalse(form.name)
        self.assertFalse(form.name_nl)

    def test_translates_values_created_by_factory_functions(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(_language="en")

        self.assertTrue(form.name_en)
        self.assertFalse(form.name)
        self.assertFalse(form.name_nl)

    def test_translates_on_build_strategy(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.build(_language="en", name="my name")

        self.assertEqual(form.name_en, "my name")
        self.assertFalse(form.name)
        self.assertFalse(form.name_nl)

    def test_is_a_noop_on_non_modeltranslate_factories(self):
        TranslatedUserFactory = make_translated(UserFactory)

        self.assertIs(TranslatedUserFactory, UserFactory)

    def test_can_still_do_explicit_passing(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(name_en="my name")

        self.assertEqual(form.name_en, "my name")
        self.assertTrue(form.name)
        self.assertEqual(form.name_nl, form.name)

    def test_ignores_non_modeltranslation_fields(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(slug="Slurm", _language="en")

        self.assertEqual(form.slug, "slurm")
        self.assertFalse(getattr(form, "slug_en", False))

    def test_does_not_try_to_set_unconfigured_languages(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.build(_language="ti", name="ስመይ")

        self.assertFalse(getattr(form, "name_ti", False))


class ISO639_2BTests(TestCase):
    def test_all_configured_languages_have_known_iso639_codes(self):
        "Document API expects ISO 639-2/B codes"
        initial_langs = {"en": "eng", "nl": "nld"}

        for language_code, _ in settings.LANGUAGES:
            with self.subTest(language_code):
                iso_code = to_iso639_2b(language_code)
                # check future codes are well formed
                self.assertEqual(len(iso_code), 3)

                # check codes we know now
                if expected := initial_langs.get(language_code, ""):
                    self.assertEqual(iso_code, expected)

    def test_new_unknown_language_raises_a_value_error(self):
        # XXX this unintentionally breaks when someone adds latin support to the function
        # exempli gratia, by replacing the dictionary lookup with a library.
        with self.assertRaisesMessage(ValueError, "Unknown language code 'la'"):
            to_iso639_2b("la")
