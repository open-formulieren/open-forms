from pprint import pprint

from django.urls import reverse

from rest_framework.test import APITestCase
from tenacity import retry, stop_after_attempt

from openforms.accounts.tests.factories import UserFactory
from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.tests.utils import log_flaky
from openforms.variables.constants import FormVariableDataTypes


class FormJsonSchemaAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    @retry(stop=stop_after_attempt(3))
    def test_happy_flow(self):
        self.maxDiff = None
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
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
                            "dataSrc": DataSrcOptions.manual,
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
                        "dataSrc": DataSrcOptions.manual,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        FormVariableFactory.create(
            form=form,
            name="Foo",
            key="foo",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "firstName": {"title": "First Name", "type": "string"},
                "lastName": {
                    "title": "Last Name",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["a", "b", ""]},
                    "title": "Select",
                },
                "selectboxes": {
                    "title": "Select boxes",
                    "type": "object",
                    "properties": {
                        "option1": {"type": "boolean"},
                        "option2": {"type": "boolean"},
                    },
                    "required": ["option1", "option2"],
                    "additionalProperties": False,
                },
                "radio": {"title": "Radio", "type": "string", "enum": ["a", "b", ""]},
                "foo": {"type": "array", "title": "Foo"},
            },
            "required": [
                "firstName",
                "lastName",
                "select",
                "selectboxes",
                "radio",
                "foo",
            ],
            "additionalProperties": False,
        }

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        generated_schema = response.json()
        if generated_schema != expected_schema:
            log_flaky()
            print("Got:")
            pprint(generated_schema)
        self.assertEqual(generated_schema, expected_schema)
