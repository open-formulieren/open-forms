from copy import deepcopy
from datetime import date

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from ..datastructures import FormioConfigurationWrapper
from ..variables import inject_variables, render

VARIABLES = {
    "html_variable": "<span>HTML injection!</span>",
    "content_timestamp": date(2022, 8, 16),
    # from json data - only use primitives!
    "labels": {
        "text1": "Label eerste textfield",
    },
    "placeholder_with_double_quotes": 'These should " be escaped',
    "defaults": {
        "text1": 123,
        "text2": 123.45,
        "number1": 0.1 + 0.1 + 0.1,
    },
    "now": timezone.now,
    "checkboxChecked": True,
}


CONFIGURATION = {
    "components": [
        {
            "type": "content",
            "key": "content1",
            "html": "<p>We expected a {{ html_variable }} to be escaped.</p>",
            "label": 'Message at {{ content_timestamp|date:"Y-m-d" }}',
        },
        {
            "type": "textfield",
            "key": "text1",
            "label": "{{ labels.text1 }}",
            "placeholder": "{{ placeholder_with_double_quotes }}",
            "defaultValue": "{{ defaults.text1 }}",
        },
        {
            "type": "textfield",
            "key": "text2",
            "defaultValue": "{{ defaults.text2 }}",
        },
        {
            "type": "textfield",
            "key": "textfieldMulti",
            "multiple": True,
            "defaultValue": [
                "{{ defaults.text1 }}",
                "{{ defaults.text2|floatformat }}",
            ],
        },
        {
            "type": "date",
            "key": "date1",
            "label": """Het is vandaag {{ now|date:"l" }}""",
            "defaultValue": "{{ now|date:'d-m-Y' }}",
        },
        {
            "type": "number",
            "key": "number1",
            # works because formio attempts to parse it as a number, even though we
            # pass a string
            "defaultValue": "{{ defaults.number1|floatformat:2 }}",
        },
        {
            "type": "checkbox",
            "key": "checkbox1",
            # this works because formio interprets 'false/true' strings as actual
            # booleans. Note that we don't expose this in the form designer UI yet!
            "defaultValue": "{{ checkboxChecked|yesno:'true,false,null' }}",
        },
    ]
}


@override_settings(LANGUAGE_CODE="nl")
@freeze_time("2022-08-16T11:57:02+02:00")
class VariableInjectionTests(SimpleTestCase):
    def test_variable_interpolation(self):
        configuration = deepcopy(CONFIGURATION)

        inject_variables(FormioConfigurationWrapper(configuration), VARIABLES)

        lookup_table = {comp["key"]: comp for comp in configuration["components"]}

        content1 = lookup_table["content1"]
        text1 = lookup_table["text1"]
        text2 = lookup_table["text2"]
        textfield_multi = lookup_table["textfieldMulti"]
        date1 = lookup_table["date1"]
        number1 = lookup_table["number1"]
        checkbox1 = lookup_table["checkbox1"]

        with self.subTest("HTML content"):
            self.assertEqual(
                content1["html"],
                "<p>We expected a &lt;span&gt;HTML injection!&lt;/span&gt; to be escaped.</p>",
            )
            self.assertEqual(content1["label"], "Message at 2022-08-16")

        with self.subTest("Nested lookups"):
            self.assertEqual(text1["label"], "Label eerste textfield")

        with self.subTest("Double quotes in placeholder escaped"):
            self.assertEqual(text1["placeholder"], "These should &quot; be escaped")

        with self.subTest("Stringified default value"):
            self.assertEqual(text1["defaultValue"], "123")

        with self.subTest("Stringified default value (float)"):
            # localized! Formio seems to handle localized values correctly
            self.assertEqual(text2["defaultValue"], "123,45")

        with self.subTest("Default values with multiple=true"):
            # localized! Formio seems to handle localized values correctly
            self.assertEqual(textfield_multi["defaultValue"], ["123", "123,5"])

        with self.subTest("Builtin template filters"):
            self.assertEqual(date1["label"], "Het is vandaag dinsdag")
            self.assertEqual(date1["defaultValue"], "16-08-2022")

        # questionable but convenient formio behaviour - it parses the string as a number
        with self.subTest("Number default floatformat, unlocalized"):
            # localized! Formio seems to handle localized values correctly.
            # We can't combine `{% localize off %}` with the floatformat template filter,
            # as the use_l10n parameter is not passed down inside of floatformat. This is fixed
            # in newer django versions than 3.2. For now, we can accept localized values.
            self.assertEqual(number1["defaultValue"], "0,30")

        # questionable but convenient formio behaviour - it parses the string as a boolean
        with self.subTest("Checkbox default value boolean-ish"):
            self.assertEqual(checkbox1["defaultValue"], "true")

    def test_custom_libraries_not_available(self):
        configuration = {
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield1",
                    "label": "{% load multidomain %}{% multidomain_switcher %}",
                }
            ]
        }

        inject_variables(FormioConfigurationWrapper(configuration), {})

        self.assertEqual(
            configuration["components"][0]["label"],
            "{% load multidomain %}{% multidomain_switcher %}",
        )

    def test_custom_builtins_not_available(self):
        configuration = {
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield1",
                    "label": "{% privacy_policy %}",
                }
            ]
        }

        inject_variables(FormioConfigurationWrapper(configuration), {})

        self.assertEqual(
            configuration["components"][0]["label"],
            "{% privacy_policy %}",
        )

    def test_rendering_nested_structures(self):
        structure = {"topLevel": {"nested": "{{ expression }}"}}
        context = {"expression": "yepp"}

        result = render(structure, context)

        self.assertEqual(
            result,
            {"topLevel": {"nested": "yepp"}},
        )

    def test_soft_required_errors_no_server_side_template_evaluation(self):
        configuration = {
            "components": [
                {
                    "key": "softRequiredErrors",
                    "type": "softRequiredErrors",
                    "html": "<p>I am hidden</p>{{ missingFields }}{% now %}",
                },
            ]
        }

        inject_variables(FormioConfigurationWrapper(configuration), {})

        self.assertEqual(
            configuration["components"][0]["html"],
            "<p>I am hidden</p>{{ missingFields }}{% now %}",
        )
