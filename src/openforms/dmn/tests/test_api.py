from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.api.tests.utils import APITestAssertions

from ..base import BasePlugin, DecisionDefinition, DecisionDefinitionVersion
from ..registry import Registry
from ..types import DMNInputOutput

register = Registry()


@register("test")
class TestPlugin(BasePlugin):
    verbose_name = "Test plugin"

    @staticmethod
    def get_available_decision_definitions():
        return [DecisionDefinition(identifier="test-1", label="Test definition")]

    @staticmethod
    def get_decision_definition_versions(definition_id: str):
        return [
            DecisionDefinitionVersion(id="v1", label="v1"),
            DecisionDefinitionVersion(id="v2", label="Version 3"),
        ]

    @staticmethod
    def get_decision_definition_parameters(
        self, definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        return {
            "inputs": [
                {
                    "id": "clause1",
                    "label": "Invoice Amount",
                    "expression": "amount",
                    "type_ref": "double",
                },
                {
                    "id": "InputClause_15qmk0v",
                    "label": "Invoice Category",
                    "expression": "invoiceCategory",
                    "type_ref": "string",
                },
            ],
            "outputs": [
                {
                    "id": "clause3",
                    "label": "Classification",
                    "name": "invoiceClassification",
                    "type_ref": "string",
                },
                {
                    "id": "OutputClause_1cthd0w",
                    "label": "Approver Group",
                    "name": "result",
                    "type_ref": "string",
                },
            ],
        }

    @staticmethod
    def evaluate(
        definition_id, *, version: str = "", input_values: dict[str, int]
    ) -> dict[str, int]:
        return {"sum": sum([input_values["a"], input_values["b"]])}


class MockRegistryMixin:
    def setUp(self):
        super().setUp()

        patcher = patch("openforms.dmn.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)


class AccessControlTests(MockRegistryMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()
        cls.admin_user = StaffUserFactory.create()

    def test_plugin_list(self):
        endpoint = reverse("api:dmn-plugin-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_list(self):
        endpoint = reverse("api:dmn-definition-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_version_list(self):
        endpoint = reverse("api:dmn-definition-version-list")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

    def test_definition_xml(self):
        endpoint = reverse("api:dmn-definition-xml")

        with self.subTest("anonymous"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated, not staff"):
            self.client.force_authenticate(user=self.user)

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("staff user"):
            self.client.force_authenticate(user=self.admin_user)

            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())


class PluginListTests(MockRegistryMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = StaffUserFactory.create()

    def test_list_response(self):
        endpoint = reverse("api:dmn-plugin-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": "test",
                    "label": "Test plugin",
                }
            ],
        )


class DefinitionEndpointTests(APITestAssertions, MockRegistryMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = StaffUserFactory.create()

    def test_list_available_definitions(self):
        endpoint = reverse("api:dmn-definition-list")
        self.client.force_authenticate(user=self.user)

        with self.subTest("Engine param is required"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "engine", "required")

        with self.subTest("Bad engine param value"):
            response = self.client.get(endpoint, {"engine": "magical-unicorn"})

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "engine", "invalid")

        with self.subTest("happy flow"):
            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(
                response.json(),
                [
                    {
                        "id": "test-1",
                        "label": "Test definition",
                    }
                ],
            )

    def test_get_available_versions(self):
        endpoint = reverse("api:dmn-definition-version-list")
        self.client.force_authenticate(user=self.user)

        with self.subTest("Engine param is required"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "engine", "required")

        with self.subTest("definition param is required"):
            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "definition", "required")

        with self.subTest("happy flow"):
            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(
                response.json(),
                [
                    {"id": "v1", "label": "v1"},
                    {"id": "v2", "label": "Version 3"},
                ],
            )

    def test_get_input_outputs(self):
        endpoint = reverse("api:dmn-definition-inputs-outputs")
        self.client.force_authenticate(user=self.user)

        with self.subTest("Engine param is required"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "engine", "required")

        with self.subTest("definition param is required"):
            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "definition", "required")

        with self.subTest("happy flow"):
            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(
                response.json(),
                {
                    "inputs": [
                        {
                            "id": "clause1",
                            "label": "Invoice Amount",
                            "expression": "amount",
                            "typeRef": "double",
                        },
                        {
                            "id": "InputClause_15qmk0v",
                            "label": "Invoice Category",
                            "expression": "invoiceCategory",
                            "typeRef": "string",
                        },
                    ],
                    "outputs": [
                        {
                            "id": "clause3",
                            "label": "Classification",
                            "name": "invoiceClassification",
                            "typeRef": "string",
                        },
                        {
                            "id": "OutputClause_1cthd0w",
                            "label": "Approver Group",
                            "name": "result",
                            "typeRef": "string",
                        },
                    ],
                },
            )


class XMLRetrieveTests(APITestAssertions, MockRegistryMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = StaffUserFactory.create()

    def test_retrieve_xml_endpoint(self):
        endpoint = reverse("api:dmn-definition-xml")
        self.client.force_authenticate(user=self.user)

        with self.subTest("Engine param is required"):
            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "engine", "required")

        with self.subTest("Definition param is required"):
            response = self.client.get(endpoint, {"engine": "test"})

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertValidationErrorCode(response, "definition", "required")

        with self.subTest("No XML available"):
            response = self.client.get(
                endpoint, {"engine": "test", "definition": "test-1"}
            )

            self.assertEqual(response.json(), {"xml": ""})
