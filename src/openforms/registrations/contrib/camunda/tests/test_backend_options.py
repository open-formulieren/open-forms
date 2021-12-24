from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.forms.tests.factories import FormFactory


class FormRegistrationBackendOptionsTests(APITestCase):
    """
    Test configuring a form with the appropriate Camunda options.

    This mostly tests the full ``CamundaOptionsSerializer``.

    TODO: add a test for a mapped variable that does not exist on the form.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = StaffUserFactory.create()
        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            registration_backend="camunda",
            formstep__form_definition__configuration=[
                {
                    "key": "test1",
                    "type": "textfield",
                },
                {
                    "key": "test2",
                    "type": "textfield",
                },
                {
                    "key": "test3",
                    "type": "textfield",
                },
            ],
        )
        cls.endpoint = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

    def test_happy_flow(self):
        """
        Assert that options are saved correctly.
        """
        detail_response = self.client.get(self.endpoint).json()
        data = {
            **detail_response,
            "registrationBackendOptions": {
                "processDefinition": "invoice",
                "processDefinitionVersion": None,
                "processVariables": [
                    {
                        "enabled": True,
                        "componentKey": "test1",
                    },
                    {
                        "enabled": False,
                        "componentKey": "test2",
                        "alias": "test2Alias",
                    },
                ],
            },
        }

        response = self.client.put(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.form.refresh_from_db()
        expected = {
            "process_definition": "invoice",
            "process_definition_version": None,
            "process_variables": [
                {
                    "enabled": True,
                    "component_key": "test1",
                    "alias": "",
                },
                {
                    "enabled": False,
                    "component_key": "test2",
                    "alias": "test2Alias",
                },
            ],
        }
        self.assertEqual(self.form.registration_backend_options, expected)
