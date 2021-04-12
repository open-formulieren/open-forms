import uuid
from unittest import expectedFailure

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Form
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormsAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

    @expectedFailure
    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()

        url = reverse("api:form-list")
        response = self.client.get(url, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        FormFactory.create_batch(2)

        url = reverse("api:form-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_post_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.filter(**data).count(), 1)

    def test_post_with_bad_data(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "bad": "data",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Form.objects.count(), 0)

    def test_post_without_authentication(self):

        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Form.objects.count(), 0)

    def test_patch_form(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Patch Form")

    def test_patch_form_without_authentication(self):
        form = FormFactory.create()
        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Patch Form")

    def test_patch_form_with_bad_data(self):
        form = FormFactory.create()
        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "bad": "data",
        }
        response = self.client.patch(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Patch Form")

    def test_patch_form_404(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = f'{reverse("api:form-list")}/{uuid.uuid4()}'
        data = {
            "bad": "data",
        }
        response = self.client.patch(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Patch Form")

    def test_put_form(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
        }
        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Put Form")

    def test_put_form_with_incomplete_data(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "name": "Test Put Form",
        }
        response = self.client.put(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"slug": ["Dit veld is vereist."]})

    def test_put_form_without_authentication(self):
        form = FormFactory.create()
        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "name": "Test Put Form",
        }
        response = self.client.put(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Put Form")

    def test_put_form_with_bad_data(self):
        form = FormFactory.create()
        url = f'{reverse("api:form-list")}/{form.uuid}'
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Put Form")

    def test_put_form_404(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = f'{reverse("api:form-list")}/{uuid.uuid4()}'
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Put Form")

    def test_steps_list(self):
        step = FormStepFactory.create()

        url = reverse("api:form-steps-list", args=(step.form.uuid,))
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class FormDefinitionsAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(), username=user.username, password="secret"
        )

    @expectedFailure
    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        FormDefinitionFactory.create_batch(2)

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["count"], 2)
