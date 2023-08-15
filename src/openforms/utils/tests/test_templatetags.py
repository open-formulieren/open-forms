from django.test import TestCase

from openforms.template import render_from_string


class TemplateTagsTests(TestCase):
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
