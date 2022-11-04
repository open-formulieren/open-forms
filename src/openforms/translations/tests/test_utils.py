from django.test import TestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory

from ..utils import make_translated


class MakeTranslatedFactoryTests(TestCase):
    def test_sets_values_for_passed_args(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(_language="en", name="my name")

        self.assertEquals(form.name_en, "my name")
        self.assertFalse(form.name)
        self.assertFalse(form.name_nl)

    def test_translates_values_created_by_factory_functions(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(_language="en")

        self.assert_(form.name_en)
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

        self.assertEquals(form.name_en, "my name")
        self.assert_(form.name)
        self.assertEquals(form.name_nl, form.name)

    def test_ignores_non_modeltranslation_fields(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.create(slug="Slurm", _language="en")

        self.assertEquals(form.slug, "slurm")
        self.assertFalse(getattr(form, "slug_en", False))

    def test_does_not_try_to_set_unconfigured_languages(self):
        TranslatedFormFactory = make_translated(FormFactory)

        form = TranslatedFormFactory.build(_language="ti", name="ስመይ")

        self.assertFalse(getattr(form, "name_ti", False))
