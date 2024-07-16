from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, override_settings

from openforms.accounts.tests.factories import UserFactory
from openforms.template import render_from_string


class TemplateTagsTests(SimpleTestCase):
    def test_get_value(self):
        result = render_from_string(
            "{% get_value a_dictionary 'a key with spaces' %} {% get_value a_dictionary 'missingKey' %} {% get_value a_dictionary 'someKey' %}",
            context={
                "a_dictionary": {
                    "a key with spaces": "an interesting value",
                    "someKey": "someValue",
                }
            },
        )

        self.assertEqual("an interesting value  someValue", result)

    def test_get_value_with_non_dictionaries(self):
        result = render_from_string(
            "{% get_value a_list 'key' %}{% get_value a_string 'key' %}",
            context={
                "a_list": ["hello"],
                "a_string": "someValue",
            },
        )

        self.assertEqual("", result)


@override_settings(SHOW_ENVIRONMENT=True)
class EnvironmentInfoTests(SimpleTestCase):

    def _render(self, context=None):
        tpl = r"{% environment_info %}"
        return render_from_string(tpl, context=context or {}).strip()

    @override_settings(SHOW_ENVIRONMENT=False)
    def test_disabled_via_settings(self):
        with self.subTest("without user"):
            result = self._render()

            self.assertEqual(result, "")

        with self.subTest("with user"):
            result = self._render({"user": UserFactory.build()})

            self.assertEqual(result, "")

    def test_anonymous_user(self):
        result = self._render({"user": AnonymousUser()})

        self.assertEqual(result, "")

    @override_settings(ENVIRONMENT_LABEL="my super duper env")
    def test_authenticated_user(self):
        result = self._render({"user": UserFactory.build()})

        self.assertNotEqual(result, "")
        self.assertInHTML("my super duper env", result)
