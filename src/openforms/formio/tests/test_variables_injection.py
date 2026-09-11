from datetime import date

from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from formio_types import (
    Content,
    Date,
    Radio,
    Select,
    Selectboxes,
    SoftRequiredErrors,
    TextField,
)
from openforms.formio.typing import Component, FieldsetComponent

from ..datastructures import FormioConfig, FormioData
from ..variables import inject_variables

VARIABLES = FormioData(
    {
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
)


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
            "label": "text2",
            "defaultValue": "{{ defaults.text2 }}",
        },
        {
            "type": "textfield",
            "key": "textfieldMulti",
            "label": "textfieldMulti",
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
        },
        # number, checkbox -> removed - our own renderer does not do the implicit type
        # casting that formiojs had, and our msgspec types don't accept template strings
        # for the default value, as that's a data type mismatch
        # date default value -> removed - our formio-builder does not support entering arbitrary
        # strings
    ]
}


@override_settings(LANGUAGE_CODE="nl")
@freeze_time("2022-08-16T11:57:02+02:00")
class VariableInjectionTests(SimpleTestCase):
    def test_variable_interpolation(self):
        formio_config = FormioConfig(
            name="<test>", components=CONFIGURATION["components"]
        )

        inject_variables(formio_config, VARIABLES)

        content1 = formio_config["content1"]
        assert isinstance(content1, Content)
        text1 = formio_config["text1"]
        assert isinstance(text1, TextField)
        text2 = formio_config["text2"]
        assert isinstance(text2, TextField)
        textfield_multi = formio_config["textfieldMulti"]
        assert isinstance(textfield_multi, TextField)
        date1 = formio_config["date1"]
        assert isinstance(date1, Date)

        with self.subTest("HTML content"):
            self.assertEqual(
                content1.html,
                "<p>We expected a &lt;span&gt;HTML injection!&lt;/span&gt; to be escaped.</p>",
            )
            self.assertEqual(content1.label, "Message at 2022-08-16")

        with self.subTest("Nested lookups"):
            self.assertEqual(text1.label, "Label eerste textfield")

        with self.subTest("Double quotes in placeholder escaped"):
            self.assertEqual(text1.placeholder, "These should &quot; be escaped")

        with self.subTest("Stringified default value"):
            self.assertEqual(text1.default_value, "123")

        with self.subTest("Stringified default value (float)"):
            # localized! Formio seems to handle localized values correctly
            self.assertEqual(text2.default_value, "123,45")

        with self.subTest("Default values with multiple=true"):
            # localized! Formio seems to handle localized values correctly
            self.assertEqual(textfield_multi.default_value, ["123", "123,5"])

        with self.subTest("Builtin template filters"):
            self.assertEqual(date1.label, "Het is vandaag dinsdag")

    def test_custom_libraries_not_available(self):
        component: Component = {
            "type": "textfield",
            "key": "textfield1",
            "label": "{% load multidomain %}{% multidomain_switcher %}",
        }
        formio_config = FormioConfig(name="<test>", components=[component])

        inject_variables(formio_config, FormioData())

        textfield = formio_config["textfield1"]
        assert isinstance(textfield, TextField)
        self.assertEqual(
            textfield.label,
            "{% load multidomain %}{% multidomain_switcher %}",
        )

    def test_custom_builtins_not_available(self):
        component: Component = {
            "type": "textfield",
            "key": "textfield1",
            "label": "{% privacy_policy %}",
        }
        formio_config = FormioConfig(name="<test>", components=[component])

        inject_variables(formio_config, FormioData())

        textfield = formio_config["textfield1"]
        assert isinstance(textfield, TextField)
        self.assertEqual(textfield.label, "{% privacy_policy %}")

    def test_rendering_nested_component_trees(self):
        component: FieldsetComponent = {
            "type": "fieldset",
            "key": "fieldset",
            "label": "fieldset",
            "components": [
                {
                    "type": "textfield",
                    "key": "textfield1",
                    "label": "{{ expression }}",
                }
            ],
        }
        formio_config = FormioConfig(name="<test>", components=[component])

        inject_variables(formio_config, FormioData({"expression": "yepp"}))

        textfield = formio_config["textfield1"]
        assert isinstance(textfield, TextField)
        self.assertEqual(textfield.label, "yepp")

    def test_soft_required_errors_no_server_side_template_evaluation(self):
        component: Component = {
            "key": "softRequiredErrors",
            "type": "softRequiredErrors",
            "html": "<p>I am hidden</p>{{ missingFields }}{% now %}",  # pyright: ignore[reportAssignmentType]
        }

        formio_config = FormioConfig(name="<test>", components=[component])

        inject_variables(formio_config, FormioData())

        soft_required = formio_config["softRequiredErrors"]
        assert isinstance(soft_required, SoftRequiredErrors)
        self.assertEqual(
            soft_required.html,
            "<p>I am hidden</p>{{ missingFields }}{% now %}",
        )

    def test_components_with_choices(self):
        components: list[Component] = [  # pyright: ignore[reportAssignmentType]
            {
                "key": "radio",
                "type": "radio",
                "label": "radio",
                "openForms": {"dataSrc": "manual"},
                "values": [
                    {
                        "value": "1",
                        "label": "{% if var == 'foo' %}1{% else %}42{% endif %}",
                    },
                    {"value": "2", "label": "2"},
                ],
            },
            {
                "key": "selectboxes",
                "type": "selectboxes",
                "label": "selectboxes",
                "openForms": {"dataSrc": "manual"},
                "values": [
                    {
                        "value": "1",
                        "label": "{% if var == 'foo' %}1{% else %}42{% endif %}",
                    },
                    {"value": "2", "label": "2"},
                ],
            },
            {
                "key": "select",
                "type": "select",
                "label": "select",
                "openForms": {"dataSrc": "manual"},
                "data": {
                    "values": [
                        {
                            "value": "1",
                            "label": "{% if var == 'foo' %}1{% else %}42{% endif %}",
                        },
                        {"value": "2", "label": "2"},
                    ]
                },
            },
        ]
        formio_config = FormioConfig(name="<test>", components=components)

        inject_variables(formio_config, FormioData({"var": "foo"}))

        radio = formio_config["radio"]
        assert isinstance(radio, Radio)
        selectboxes = formio_config["selectboxes"]
        assert isinstance(selectboxes, Selectboxes)
        select = formio_config["select"]
        assert isinstance(select, Select)
        self.assertEqual(radio.values[0].label, "1")
        self.assertEqual(selectboxes.values[0].label, "1")
        self.assertEqual(select.data.values[0].label, "1")
