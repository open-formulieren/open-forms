import json
from datetime import UTC, datetime, timedelta

from django.test import override_settings
from django.urls import reverse

import time_machine
from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APIRequestFactory, APITestCase

from openforms.accounts.tests.factories import TokenFactory, UserFactory
from openforms.forms.tests.factories import FormFactory

from ..constants import SupportedAuthAttributes
from ..models import InitialSubmissionData


class InitialDataAccessControlTests(APITestCase):
    endpoint = reverse_lazy("api:initial-data-list")

    def test_no_access_without_credentials(self):
        response = self.client.post(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_access_with_session_auth(self):
        UserFactory.create(
            username="test",
            password="supersecret",
            user_permissions=["initial_data.add_initialsubmissiondata"],
        )
        rf = APIRequestFactory()
        self.client.login(
            username="test", password="supersecret", request=rf.post("/login")
        )

        response = self.client.post(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_access_with_token_but_missing_permissions(self):
        user = UserFactory.create(user_permissions=[])
        token = TokenFactory(user=user)

        response = self.client.post(
            self.endpoint, headers={"Authorization": f"Token {token.key}"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_access_with_token_and_add_permission(self):
        user = UserFactory.create(
            user_permissions=["initial_data.add_initialsubmissiondata"]
        )
        token = TokenFactory(user=user)

        response = self.client.post(
            self.endpoint, headers={"Authorization": f"Token {token.key}"}
        )

        self.assertNotIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class CreateInitialDataTests(APITestCase):
    endpoint = reverse_lazy("api:initial-data-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(
            user_permissions=["initial_data.add_initialsubmissiondata"]
        )
        token = TokenFactory(user=cls.user)

        cls.auth_header = {"Authorization": f"Token {token.key}"}

    @time_machine.travel("2026-10-15T11:59:00+01:00")
    def test_create_initial_data_minimal_data(self):
        form = FormFactory.create()
        data = {
            "form": str(form.uuid),
            "representee": {
                "authAttribute": SupportedAuthAttributes.bsn,
                "value": "999993380",
            },
            "ttl": 3,
        }

        response = self.client.post(self.endpoint, data, headers=self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        initial_data = InitialSubmissionData.objects.get()
        self.assertEqual(initial_data.form, form)
        self.assertEqual(initial_data.ttl, timedelta(hours=3))
        self.assertEqual(initial_data.owner, self.user)

        response_data = response.json()

        with self.subTest("uuid reference"):
            self.assertEqual(response_data["uuid"], str(initial_data.uuid))

        with self.subTest("expiry date"):
            # expect an expiry date ~ 3 hours in the future
            expires_at = datetime.fromisoformat(response_data["expiresAt"])
            self.assertGreaterEqual(
                expires_at, datetime(2026, 10, 15, 10, 59, 0, tzinfo=UTC)
            )
            self.assertLessEqual(
                expires_at, datetime(2026, 10, 15, 13, 59, 5, tzinfo=UTC)
            )

        with self.subTest("redirect URL"):
            redirect_url = furl(response_data["redirectUrl"])

            self.assertEqual(redirect_url.host, "testserver")
            self.assertEqual(
                redirect_url.path,
                reverse("core:form-detail", kwargs={"slug": form.slug}),
            )
            self.assertEqual(redirect_url.args["_of_action"], "init")
            _params_str = redirect_url.args["_of_action_params"]
            assert isinstance(_params_str, str)
            action_params = json.loads(_params_str)
            self.assertEqual(action_params["representee_ref"], str(initial_data.uuid))
            # XXX: not sure if token adds any security here if we have the data in the
            # DB already anyway. Probably it makes more sense to correlate a submission
            # with an initial data record to prevent replays that way? TBD
            # self.assertIn("token", action_params)

        with self.subTest("write-only data omitted in response"):
            self.assertEqual(
                set(response_data.keys()), {"uuid", "redirectUrl", "expiresAt"}
            )

    def test_can_provide_optional_kvk_branch_number(self):
        form = FormFactory.create()
        data = {
            "form": str(form.uuid),
            "representee": {
                "authAttribute": SupportedAuthAttributes.kvk,
                "value": "12345678",
                "branchNumber": "123456123456",
            },
            "ttl": 1,
        }

        response = self.client.post(self.endpoint, data, headers=self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        initial_data = InitialSubmissionData.objects.get()

        self.assertEqual(
            initial_data.representee_auth_attribute, SupportedAuthAttributes.kvk
        )
        self.assertEqual(initial_data.representee_auth_value, "12345678")
        self.assertEqual(initial_data.representee_branch_number, "123456123456")

    def test_create_initial_data_with_custom_url_not_in_cors_policy(self):
        form = FormFactory.create()
        data = {
            "form": str(form.uuid),
            "formUrl": "https://evil.com/some-form",
            "representee": {
                "authAttribute": SupportedAuthAttributes.bsn,
                "value": "999993380",
            },
            "ttl": 1,
        }

        response = self.client.post(self.endpoint, data, headers=self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["name"], "formUrl")
        self.assertEqual(error["code"], "invalid")

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_create_initial_data_with_custom_url(self):
        form = FormFactory.create()
        data = {
            "form": str(form.uuid),
            "formUrl": "https://example.com/some-cms-page/form/",
            "representee": {
                "authAttribute": SupportedAuthAttributes.bsn,
                "value": "999993380",
            },
            "ttl": 1,
        }

        response = self.client.post(self.endpoint, data, headers=self.auth_header)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        initial_data = InitialSubmissionData.objects.get()

        with self.subTest("redirect URL"):
            redirect_url = furl(response_data["redirectUrl"])

            self.assertEqual(redirect_url.host, "example.com")
            self.assertEqual(redirect_url.path, "/some-cms-page/form/")
            self.assertEqual(redirect_url.args["_of_action"], "init")
            _params_str = redirect_url.args["_of_action_params"]
            assert isinstance(_params_str, str)
            action_params = json.loads(_params_str)
            self.assertEqual(action_params["representee_ref"], str(initial_data.uuid))
