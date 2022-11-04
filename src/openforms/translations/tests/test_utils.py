from django.test import TestCase, override_settings

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory

from ..utils import make_fully_translated


class MakeFullyTranslatedFactoryTests(TestCase):
    def test_sets_values_for_passed_args(self):
        TranslatedFormFactory = make_fully_translated(FormFactory)

        form = TranslatedFormFactory.create(name="my name")

        self.assertEquals(form.name_en, "en_my name")
        self.assertEquals(form.name_nl, "nl_my name")

    @override_settings(LANGUAGE_CODE="en")
    def test_translates_values_created_by_factory_functions(self):
        TranslatedFormFactory = make_fully_translated(FormFactory)

        form = TranslatedFormFactory.create()

        sequenced_name = form.name
        self.assertEquals(form.name_en, sequenced_name)
        self.assertEquals(form.name_nl, f"nl{sequenced_name[2:]}")

    def test_translates_on_build_strategy(self):
        TranslatedFormFactory = make_fully_translated(FormFactory)

        form = TranslatedFormFactory.build(name="my name")

        self.assertEquals(form.name_en, "en_my name")
        self.assertEquals(form.name_nl, "nl_my name")

    def test_is_a_noop_on_non_modeltranslate_factories(self):
        TranslatedUserFactory = make_fully_translated(UserFactory)

        self.assertIs(TranslatedUserFactory, UserFactory)
