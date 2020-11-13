from unittest import expectedFailure

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormsAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(
            username="john",
            password="secret",
            email="john@example.com"
        )

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(),
            username=user.username,
            password="secret"
        )

    @expectedFailure
    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()

        url = reverse('api:form-list')
        response = self.client.get(url, format='json', secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        FormFactory.create_batch(2)

        url = reverse('api:form-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_steps_list(self):
        step = FormStepFactory.create()

        url = reverse('api:form-steps-list', args=(step.form.uuid,))
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class FormDefinitionsAPITests(APITestCase):

    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(
            username="john",
            password="secret",
            email="john@example.com"
        )

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(),
            username=user.username,
            password="secret"
        )

    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()

        url = reverse('api:formdefinition-list')
        response = self.client.get(url, format='json', secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        FormDefinitionFactory.create_batch(2)

        url = reverse('api:formdefinition-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
