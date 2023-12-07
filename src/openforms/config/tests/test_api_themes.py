from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.models import Form

from .factories import ThemeFactory


class ThemesAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(is_staff=True)

    def test_access_control(self):
        url = reverse("api:themes-list")

        with self.subTest("anonymous user"):
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        with self.subTest("non-staff user"):
            user = UserFactory.create()
            assert not user.is_staff
            self.client.force_authenticate(user=user)

            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_write_themes_via_api(self):
        url = reverse("api:themes-list")
        self.client.force_authenticate(user=self.user)

        with self.subTest(method="POST"):
            response = self.client.post(url, {"name": "A theme"})

            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        with self.subTest(method="PUT"):
            response = self.client.put(url, {"name": "A theme"})

            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        with self.subTest(method="PATCH"):
            response = self.client.patch(url, {"name": "A theme"})

            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_detail(self):
        theme = ThemeFactory.create(name="A team")
        url = reverse("api:themes-detail", args=[theme.uuid])
        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(
            data,
            {
                "url": f"http://testserver{url}",
                "name": "A team",
            },
        )

    def test_list(self):
        ThemeFactory.create_batch(5)
        url = reverse("api:themes-list")
        self.client.force_authenticate(user=self.user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 5)
        self.assertIsInstance(data, list)  # no pagination dict
        self.assertIn("url", data[0])
        self.assertIn("name", data[0])

    def test_create_form_with_theme(self):
        user = UserFactory.create(is_staff=True, user_permissions=["change_form"])
        theme = ThemeFactory.create()
        theme_url = reverse("api:themes-detail", kwargs={"uuid": theme.uuid})
        url = reverse("api:form-list")
        self.client.force_authenticate(user=user)

        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "theme": theme_url,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.theme, theme)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["theme"], f"http://testserver{theme_url}")
