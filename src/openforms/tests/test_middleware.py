from django.test import TestCase

from rest_framework.reverse import reverse

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.middleware import (
    CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME,
    CSRF_TOKEN_HEADER_NAME,
)


class CSRFTokenMiddleware(TestCase):
    def test_csrftoken_in_header_api_endpoint(self):
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CSRF_TOKEN_HEADER_NAME, response.headers)

    def test_csrftoken_not_in_header_root(self):
        response = self.client.get("/")

        self.assertNotIn(CSRF_TOKEN_HEADER_NAME, response.headers)


class CanNavigateBetweenStepsMiddlewareTests(TestCase):
    def test_header_api_endpoint_not_authenticated(self):
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME, response.headers)
        self.assertEqual(
            "false", response.headers[CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME]
        )

    def test_header_not_api_endpoint_not_authenticated(self):
        response = self.client.get("/")

        self.assertNotIn(CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME, response.headers)

    def test_header_api_endpoint_superuser(self):
        user = SuperUserFactory.create()
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME, response.headers)
        self.assertEqual(
            "true", response.headers[CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME]
        )

    def test_header_api_endpoint_staff_without_permissions(self):
        user = StaffUserFactory.create()
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME, response.headers)
        self.assertEqual(
            "false", response.headers[CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME]
        )

    def test_header_api_endpoint_staff_with_permissions(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME, response.headers)
        self.assertEqual(
            "true", response.headers[CAN_NAVIGATE_BETWEEN_STEPS_HEADER_NAME]
        )
