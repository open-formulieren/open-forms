from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.authentication.constants import AuthAttribute

from ...constants import FormVariableDataTypes, FormVariableSources
from ...models import FormVariable
from ..factories import FormFactory, FormVariableFactory


# TODO Remove once the FormLogicViewSet endpoint is removed
@override_settings(LANGUAGE_CODE="en")
class VariablesInLogicAPITests(APITestCase):
    def test_user_defined_variable_in_trigger(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined, key="testUserDefined", form=form
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "order": 0,
            "json_logic_trigger": {
                "==": [
                    {"var": "testUserDefined"},
                    "some test value",
                ]
            },
            "actions": [
                {
                    "action": {
                        "type": "disable-next",
                    }
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_invalid_user_defined_variable_in_trigger(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined, key="testUserDefined", form=form
        )

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "order": 0,
            "json_logic_trigger": {
                "==": [
                    {"var": "invalidTestUserDefined"},
                    "some test value",
                ]
            },
            "actions": [
                {
                    "action": {
                        "type": "disable-next",
                    }
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual("invalid", error["code"])
        self.assertEqual("jsonLogicTrigger", error["invalidParams"][0]["name"])
        self.assertEqual(
            "The specified variable is not related to the form",
            error["invalidParams"][0]["reason"],
        )

    @patch(
        "openforms.forms.models.FormVariable.get_static_data",
        return_value=[FormVariable(key="now")],
    )
    def test_static_variable_in_trigger(self, m_get_static_data):
        user = SuperUserFactory.create()
        form = FormFactory.create()

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "order": 0,
            "json_logic_trigger": {
                "==": [
                    {"var": "now"},
                    "2021-07-16T21:15:00+00:00",
                ]
            },
            "actions": [
                {
                    "action": {
                        "type": "disable-next",
                    }
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    @patch(
        "openforms.forms.models.FormVariable.get_static_data",
        return_value=[
            FormVariable(
                name="Authentication identifier",
                key="auth_identifier",
                data_type=FormVariableDataTypes.object,
                initial_value={
                    "plugin": "digid",
                    "attribute": AuthAttribute.bsn,
                    "value": "123456782",
                },
            )
        ],
    )
    def test_auth_static_variable_in_trigger(self, m_get_static_data):
        user = SuperUserFactory.create()
        form = FormFactory.create()

        form_logic_data = {
            "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
            "order": 0,
            "json_logic_trigger": {
                "==": [
                    {"var": "auth_identifier.plugin"},
                    "digid",
                ]
            },
            "actions": [
                {
                    "action": {
                        "type": "disable-next",
                    }
                }
            ],
        }

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)


@override_settings(LANGUAGE_CODE="en")
class VariablesInLogicBulkAPITests(APITestCase):
    def test_user_defined_variable_in_trigger(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined, key="testUserDefined", form=form
        )

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {
                    "==": [
                        {"var": "testUserDefined"},
                        "some test value",
                    ]
                },
                "actions": [
                    {
                        "action": {
                            "type": "disable-next",
                        }
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_invalid_user_defined_variable_in_trigger(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined, key="testUserDefined", form=form
        )

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {
                    "==": [
                        {"var": "invalidTestUserDefined"},
                        "some test value",
                    ]
                },
                "actions": [
                    {
                        "action": {
                            "type": "disable-next",
                        }
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual("invalid", error["code"])
        self.assertEqual("0.jsonLogicTrigger", error["invalidParams"][0]["name"])
        self.assertEqual(
            "The specified variable is not related to the form",
            error["invalidParams"][0]["reason"],
        )

    @patch(
        "openforms.forms.models.FormVariable.get_static_data",
        return_value=[FormVariable(key="now")],
    )
    def test_static_variable_in_trigger(self, m_get_static_data):
        user = SuperUserFactory.create()
        form = FormFactory.create()

        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {
                    "==": [
                        {"var": "now"},
                        "2021-07-16T21:15:00+00:00",
                    ]
                },
                "actions": [
                    {
                        "action": {
                            "type": "disable-next",
                        }
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
