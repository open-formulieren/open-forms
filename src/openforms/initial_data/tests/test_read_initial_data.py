from datetime import datetime

from django.utils import timezone

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from openforms.accounts.tests.factories import TokenFactory, UserFactory

from .factories import InitialSubmissionDataFactory


class InitialDataAccessControlTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(
            username="test",
            password="supersecret",
            user_permissions=["initial_data.add_initialsubmissiondata"],
        )
        initial_data = InitialSubmissionDataFactory.create(owner=cls.user)
        cls.endpoint = reverse(
            "api:initial-data-detail", kwargs={"uuid": initial_data.uuid}
        )

    def test_no_access_without_credentials(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_access_with_session_auth(self):
        rf = APIRequestFactory()
        self.client.login(
            username="test", password="supersecret", request=rf.post("/login")
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_lookup_initial_data_owner_by_others(self):
        user = UserFactory.create(user_permissions=[])
        token = TokenFactory(user=user)

        response = self.client.get(
            self.endpoint,
            headers={"Authorization": f"Token {token.key}"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_has_access_with_token_and_is_owner(self):
        token = TokenFactory(user=self.user)

        response = self.client.get(
            self.endpoint,
            headers={"Authorization": f"Token {token.key}"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReadInitialDataTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(
            user_permissions=["initial_data.add_initialsubmissiondata"]
        )
        token = TokenFactory(user=cls.user)

        cls.auth_header = {"Authorization": f"Token {token.key}"}

    def test_detail_endpoint_exposes_minimal_information(self):
        initial_data = InitialSubmissionDataFactory.create(owner=self.user)
        endpoint = reverse(
            "api:initial-data-detail", kwargs={"uuid": initial_data.uuid}
        )

        response = self.client.get(endpoint, headers=self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            set(response_data.keys()), {"uuid", "redirectUrl", "expiresAt"}
        )
        expires_at = datetime.fromisoformat(response_data["expiresAt"])
        self.assertGreater(expires_at, timezone.now())

    def test_cannot_list_initial_data(self):
        response = self.client.get(
            reverse("api:initial-data-list"), headers=self.auth_header
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
