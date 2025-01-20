from django.test import TestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.forms.utils import (
    form_variables_to_json_schema,
    get_json_schema_from_form_variable,
    is_form_variable_required,
)
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class FormToJsonSchemaTestCase(TestCase):
    def test_correct_variables_included_in_schema(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                    {
                        "key": "lastName",
                        "type": "textfield",
                        "multiple": True,
                        "label": "Last Name",
                    },
                    {
                        "label": "Select",
                        "key": "select",
                        "data": {
                            "values": [
                                {"label": "A", "value": "a"},
                                {"label": "B", "value": "b"},
                            ],
                            "dataSrc": "manual",
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                        "type": "select",
                        "multiple": True,
                    },
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ],
                    },
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "dataSrc": "manual",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        form_def_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "file",
                        "type": "file",
                        "label": "File",
                        "validate": {"required": True},
                    },
                    {
                        "key": "notIncluded",
                        "type": "textfield",
                        "label": "Not included text field",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_2)

        vars_to_include = (
            "firstName",
            "lastName",
            "select",
            "selectboxes",
            "radio",
            "file",
            "auth_bsn",
            "today",
        )
        schema = form_variables_to_json_schema(form, vars_to_include)

        self.assertEqual(set(schema["properties"]), set(vars_to_include))
        self.assertEqual(schema["required"], ["auth_bsn", "today", "file"])


# TODO-4980: add to variables app if get_json_schema_from_form_variable is moved to
#  FormVariable
class TestGetJsonSchemaFromFormVariableTests(TestCase):

    def test_component(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Foo",
                        "source": FormVariableSources.component,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        var = form_def.formvariable_set.first()
        schema = get_json_schema_from_form_variable(var)

        expected_schema = {"title": "Foo", "type": "string"}
        self.assertEqual(schema, expected_schema)

    def test_user_defined(self):
        var = FormVariableFactory.create(
            name="Foo",
            key="foo",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        schema = get_json_schema_from_form_variable(var)

        expected_schema = {"title": "Foo", "type": "array"}
        self.assertEqual(schema, expected_schema)


# TODO-4980: add to variables app if is_form_variable_required is moved toFormVariable
class TestIsFormVariableRequired(TestCase):

    def test_component_default(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Foo",
                        "source": FormVariableSources.component,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        var = form_def.formvariable_set.first()
        required = is_form_variable_required(var)

        self.assertFalse(required)

    def test_component_required(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Foo",
                        "source": FormVariableSources.component,
                        "validate": {"required": True},
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        var = form_def.formvariable_set.first()
        required = is_form_variable_required(var)

        self.assertTrue(required)

    def test_user_defined(self):
        var = FormVariableFactory.create(
            name="Foo",
            key="foo",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        required = is_form_variable_required(var)

        self.assertTrue(required)
