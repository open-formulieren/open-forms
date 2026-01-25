from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.authentication.service import AuthAttribute
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.registry import Registry

from ..factories import FormFactory, FormVariableFactory


class DemoNow(BaseStaticVariable):
    name = "Now"
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, *args, **kwargs):
        return "2021-07-16T21:15:00+00:00"


class DemoAuth(BaseStaticVariable):
    name = "Authentication identifier"
    data_type = FormVariableDataTypes.object

    def get_initial_value(self, *args, **kwargs):
        return {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }


register = Registry()
register("now")(DemoNow)
register("auth")(DemoAuth)


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
                        "action": {"type": "set-registration-backend", "value": "foo"},
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
                        "action": {"type": "set-registration-backend", "value": "foo"},
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

    def test_invalid_date_format_for_user_defined_variable(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="date_var",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
        form_logic_data = [
            {
                "form": f"http://testserver{reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})}",
                "order": 0,
                "json_logic_trigger": {"!!": [True]},
                "actions": [
                    {
                        "variable": "date_var",
                        "action": {
                            "type": "variable",
                            "value": "07-03-2023",  # not isoformat
                        },
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
        self.assertEqual(
            "Value for date variable must be a string in the format yyyy-mm-dd (e.g. 2023-07-03)",
            error["invalidParams"][0]["reason"],
        )
        self.assertEqual(error["invalidParams"][0]["name"], "0.actions.0.action.value")

    def test_valid_date_format_for_user_defined_variable(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        FormVariableFactory.create(
            source=FormVariableSources.user_defined,
            key="date_var",
            form=form,
            data_type=FormVariableDataTypes.date,
        )
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
                        "variable": "date_var",
                        "action": {
                            "type": "variable",
                            "value": "2023-03-07",  # isoformat
                        },
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_static_variable_in_trigger(self):
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
                        "action": {"type": "set-registration-backend", "value": "foo"},
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        with patch(
            "openforms.variables.service.static_variables_registry", new=register
        ):
            response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
