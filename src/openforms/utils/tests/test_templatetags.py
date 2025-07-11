from django.test import SimpleTestCase

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
