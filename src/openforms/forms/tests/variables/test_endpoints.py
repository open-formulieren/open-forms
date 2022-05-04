from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.constants import FormVariablesDataTypes, FormVariablesSources
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import FormDefinitionFactory, FormFactory


class FormVariablesViewsetTests(APITestCase):
    def test_bulk_create_variables(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create()

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "Name",
                "source": FormVariablesSources.component,
                "data_type": FormVariablesDataTypes.inferred_from_component,
                "initial_value": {},
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "Today",
                "source": FormVariablesSources.static,
                "data_type": FormVariablesDataTypes.datetime,
                "initial_value": {},
            },
        ]

        variables_url = reverse("api:form-variables-list")
        self.client.force_authenticate(user)
        response = self.client.post(variables_url, data=data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        form_variables = FormVariable.objects.all()

        self.assertEqual(2, form_variables.count())

    def test_bulk_create_or_update_variables(self):
        pass
