from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.authentication.constants import AuthAttribute
from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources
from openforms.variables.registry import Registry

from ..factories import FormFactory, FormVariableFactory


class DemoNow(BaseStaticVariable):
    name = "Now"
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, *args, **kwargs):
        return "2021-07-16T21:15:00+00:00"


class DemoAuthIdentifier(BaseStaticVariable):
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
register("auth_identifier")(DemoAuthIdentifier)


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

    def test_static_variable_in_trigger(self):
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

        with patch("openforms.variables.service.register", new=register):
            response = self.client.post(url, data=form_logic_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_auth_static_variable_in_trigger(self):
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

        with patch("openforms.variables.service.register", new=register):
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
                        "action": {
                            "type": "disable-next",
                        }
                    }
                ],
            }
        ]

        self.client.force_authenticate(user=user)
        url = reverse("api:form-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        with patch("openforms.variables.service.register", new=register):
            response = self.client.put(url, data=form_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
