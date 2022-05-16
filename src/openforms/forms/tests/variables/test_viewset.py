from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.forms.constants import FormVariablesDataTypes, FormVariablesSources
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormVariableFactory,
)


class FormVariableViewsetTest(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        url = reverse(
            "api:form-variables-bulk-update",
            kwargs={"form_uuid_or_slug": form.uuid},
        )

        response = self.client.put(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["change_form", "view_form"]
        )
        form = FormFactory.create()
        url = reverse(
            "api:form-variables-bulk-update",
            kwargs={"form_uuid_or_slug": form.uuid},
        )

        self.client.force_authenticate(user=user)
        response = self.client.put(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_bulk_create_and_update(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create()

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        form_variable1 = FormVariableFactory.create(
            form=form, form_definition=form_definition
        )
        form_variable2 = FormVariableFactory.create(
            form=form, form_definition=form_definition
        )  # This variable will be deleted
        another_form_variable = (
            FormVariableFactory.create()
        )  # Not related to the same form!

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": form_variable1.key,
                "name": "Test",
                "source": form_variable1.source,
                "data_type": form_variable1.data_type,
                "initial_value": form_variable1.initial_value,
            },  # Data of form_variable1
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "Today",
                "key": "today",
                "source": FormVariablesSources.static,
                "data_type": FormVariablesDataTypes.datetime,
                "initial_value": "today",
            },  # New variable
        ]

        self.client.force_authenticate(user)
        response = self.client.put(
            reverse(
                "api:form-variables-bulk-update",
                kwargs={"form_uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        variables = FormVariable.objects.all()

        self.assertEqual(3, variables.count())
        self.assertTrue(variables.filter(key=another_form_variable.key).exists())

        form_variables = variables.filter(form=form)

        self.assertEqual(2, form_variables.count())
        self.assertTrue(form_variables.filter(key="today").exists())
        self.assertTrue(form_variables.filter(key=form_variable1.key).exists())
        self.assertFalse(form_variables.filter(key=form_variable2.key).exists())

    @override_settings(LANGUAGE_CODE="en")
    def test_unique_together_key_form(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
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
                "key": "test-not-unique",
                "name": "Test 1",
                "source": FormVariablesSources.static,
                "data_type": FormVariablesDataTypes.string,
                "initial_value": "",
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "Test 2",
                "key": "test-not-unique",
                "source": FormVariablesSources.static,
                "data_type": FormVariablesDataTypes.string,
                "initial_value": "",
            },
        ]

        self.client.force_authenticate(user)
        response = self.client.put(
            reverse(
                "api:form-variables-bulk-update",
                kwargs={"form_uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual(error["code"], "invalid")
        self.assertEqual(
            error["invalidParams"][0]["reason"],
            "The form and key attributes must be unique together",
        )
