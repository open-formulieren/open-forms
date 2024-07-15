from django.conf import settings
from django.test import TestCase

from ..utils import to_iso639_2b


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
