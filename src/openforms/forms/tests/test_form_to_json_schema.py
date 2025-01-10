from django.test import TestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.forms.utils import form_variables_to_json_schema


class FormToJsonSchemaTestCase(TestCase):
    def test_form_to_json_schema(self):
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
        form_step_1 = FormStepFactory.create(form=form, form_definition=form_def_1)

        form_def_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "file", "type": "file", "label": "File"},
                ]
            }
        )
        form_step_2 = FormStepFactory.create(form=form, form_definition=form_def_2)

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

    def test_select_component_with_form_variable_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Select",
                        "key": "select",
                        "type": "select",
                        "openForms": {
                            "dataSrc": "variable",
                            "translations": {},
                            "itemsExpression": {"var": "valuesForSelect"}
                        },
                        "data": {
                            "values": [],
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                    },
                ]
            }
        )
        form_step_1 = FormStepFactory.create(form=form, form_definition=form_def_1)

        FormVariableFactory.create(
            form=form,
            name="Values for select",
            key="valuesForSelect",
            user_defined=True,
            initial_value=["A", "B", "C"]
        )

        schema = form_variables_to_json_schema(form, ["select"])

        self.assertEqual(schema["properties"]["select"]["enum"], ["A", "B", "C"])

    def test_select_boxes_component_with_form_variable_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Select Boxes",
                        "key": "selectBoxes",
                        "type": "selectboxes",
                        "openForms": {
                            "dataSrc": "variable",
                            "translations": {},
                            "itemsExpression": {"var": "valuesForSelectBoxes"}
                        },
                        "values": []
                    },
                ]
            }
        )
        form_step_1 = FormStepFactory.create(form=form, form_definition=form_def_1)

        FormVariableFactory.create(
            form=form,
            name="Values for select",
            key="valuesForSelect",
            user_defined=True,
            initial_value=["A", "B", "C"]
        )

        schema = form_variables_to_json_schema(form, ["selectBoxes"])

        self.assertEqual(
            schema["properties"]["selectBoxes"]["properties"],
            {
                "A": {"type": "boolean"},
                "B": {"type": "boolean"},
                "C": {"type": "boolean"},
            }
        )
        self.assertEqual(schema["properties"]["selectBoxes"]["required"], ["A", "B", "C"])
