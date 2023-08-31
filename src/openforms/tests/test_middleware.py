from django.test import TestCase

from rest_framework.reverse import reverse

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.middleware import CSRF_TOKEN_HEADER_NAME, IS_FORM_DESIGNER_HEADER_NAME


class CSRFTokenMiddleware(TestCase):
    def test_csrftoken_in_header_api_endpoint(self):
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(CSRF_TOKEN_HEADER_NAME, response.headers)

    def test_csrftoken_not_in_header_root(self):
        response = self.client.get("/")

        self.assertNotIn(CSRF_TOKEN_HEADER_NAME, response.headers)

    def test_csrftoken_in_header_api_endpoint_with_subpath(self):
        url = reverse("api:form-list")

        response = self.client.get(url, SCRIPT_NAME="/of")

        self.assertIn(CSRF_TOKEN_HEADER_NAME, response.headers)

    def test_csrftoken_not_in_header_root_with_subpath(self):
        response = self.client.get("/", SCRIPT_NAME="/of")

        self.assertNotIn(CSRF_TOKEN_HEADER_NAME, response.headers)


class CanNavigateBetweenStepsMiddlewareTests(TestCase):
    def test_header_api_endpoint_not_authenticated(self):
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertNotIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)

    def test_header_not_api_endpoint_not_authenticated(self):
        response = self.client.get("/")

        self.assertNotIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)

    def test_header_api_endpoint_superuser(self):
        user = SuperUserFactory.create()
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)
        self.assertEqual("true", response.headers[IS_FORM_DESIGNER_HEADER_NAME])

    def test_header_api_endpoint_staff_without_permissions(self):
        user = StaffUserFactory.create()
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)
        self.assertEqual("false", response.headers[IS_FORM_DESIGNER_HEADER_NAME])

    def test_header_api_endpoint_staff_with_permissions(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url)

        self.assertIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)
        self.assertEqual("true", response.headers[IS_FORM_DESIGNER_HEADER_NAME])

    def test_header_not_api_endpoint_with_subpath(self):
        response = self.client.get("/", SCRIPT_NAME="/of")

        self.assertNotIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)

    def test_header_api_endpoint_staff_with_permissions_with_subpath(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_login(user=user)
        url = reverse("api:form-list")

        response = self.client.get(url, SCRIPT_NAME="/of")

        self.assertIn(IS_FORM_DESIGNER_HEADER_NAME, response.headers)
        self.assertEqual("true", response.headers[IS_FORM_DESIGNER_HEADER_NAME])
