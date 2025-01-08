from django.test import TestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
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
