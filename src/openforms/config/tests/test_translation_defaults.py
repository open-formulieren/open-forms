from django.test import TestCase

from ..models import GlobalConfiguration
from ..translation import GlobalConfigurationTranslationOptions


class TranslatableFieldDefaultsTests(TestCase):
    relevant_fields = GlobalConfigurationTranslationOptions.fields

    def test_field_default_produces_different_translations_per_language(self):
        unsaved_instance = GlobalConfiguration()
        for field in self.relevant_fields:
            model_field = GlobalConfiguration._meta.get_field(field)

            with self.subTest(model_field=field):
                is_safe_default = callable(default := model_field.default) or (
                    not default
                )
                # if the default is not callable and not-empty, but translatable, then every
                # supported language will have the same value and won't take the field language
                # into account.
                self.assertTrue(
                    is_safe_default,
                    "Translatable model fields must have a callable or empty-ish default.",
                )
                if not callable(default):
                    continue

                value_en = getattr(unsaved_instance, f"{field}_en")
                value_nl = getattr(unsaved_instance, f"{field}_nl")
                self.assertNotEqual(
                    value_en,
                    value_nl,
                    "Different languages produce the same value - check that your "
                    "translations catalog is up to date and that your dynamic default "
                    "actually returns translatable values!",
                )
