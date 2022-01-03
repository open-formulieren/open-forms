from django.test import TestCase
from django.urls import reverse

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory


class ConfigCheckTests(TestCase):
    def setUp(self):
        super().setUp()

    def test_access_permission(self):
        url = reverse("config:overview")
        with self.subTest("anon"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

        with self.subTest("user"):
            self.client.force_login(UserFactory())
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

        with self.subTest("staff"):
            self.client.force_login(StaffUserFactory())
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

        with self.subTest("staff with permission"):
            user = StaffUserFactory(user_permissions=["configuration_overview"])
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
