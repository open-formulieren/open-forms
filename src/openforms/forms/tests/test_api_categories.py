from django.contrib.auth.models import Permission
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from ...accounts.tests.factories import UserFactory
from ..models import Category, Form
from .factories import CategoryFactory


class CategoriesAPITests(APITestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        self.client.force_authenticate(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

    def test_detail(self):
        category_1 = Category.add_root(name="foo")
        category_2 = category_1.add_child(name="bar")

        url = reverse("api:categories-detail", args=[category_2.uuid])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "bar")
        self.assertEqual(data["url"], "http://testserver" + url)
        self.assertEqual(data["uuid"], str(category_2.uuid))

        self.assertEqual(len(data["ancestors"]), 1)
        self.assertEqual(data["ancestors"][0]["name"], "foo")
        self.assertEqual(data["ancestors"][0]["uuid"], str(category_1.uuid))

    def test_list(self):
        category_1 = Category.add_root(name="foo")
        category_1.add_child(name="bar")

        url = reverse("api:categories-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "foo")
        self.assertEqual(data[1]["name"], "bar")

        self.assertEqual(len(data[1]["ancestors"]), 1)
        self.assertEqual(data[1]["ancestors"][0]["name"], "foo")

    def test_create_form_with_category(self):
        category = CategoryFactory.create()
        category_url = reverse("api:categories-detail", args=[category.uuid])
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
            "category": category_url,
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.category.pk, category.pk)

        url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["category"], "http://testserver" + category_url
        )
