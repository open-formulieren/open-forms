from django.test import SimpleTestCase, TestCase, override_settings

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory

from ..utils import get_translatable_drf_views, make_fully_translated


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


class TranslatabableDRFViewsTests(SimpleTestCase):
    def test_forms_api_endpoint_is_translatable(self):
        self.assertNotIn(
            "openforms.forms.api.viewsets.FormViewSet",
            dir(),
            msg="The test shouldn't have imported the FormViewSet in the namespace",
        )

        translatable = get_translatable_drf_views()

        names = {f"{view.__module__}.{view.__name__}" for view in translatable}

        self.assertIn("openforms.forms.api.viewsets.FormViewSet", names)
        self.assertIn("openforms.forms.api.viewsets.FormViewSet", names)
