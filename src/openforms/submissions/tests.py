from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.urls import reverse
from django.http import HttpRequest

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.core.models import Form
from .models import Submission


class SubmissionAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(username="john", password="secret", email="john@example.com")

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        self.client.login(request=HttpRequest(), username=user.username, password="secret")

    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()
        
        url = reverse('api:submission-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        # TODO: Replace with factory
        form = Form.objects.create(
            name="test",
            slug="test",
        )

        # TODO: Replace with factory
        submission = Submission.objects.create(
            form=form,
        )

        url = reverse('api:submission-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_create(self):
        # TODO: Replace with factory
        form = Form.objects.create(
            name="test",
            slug="test",
        )
       
        url = reverse('api:submission-list')
        data = {
            "form": reverse('api:form-detail', kwargs={'slug': form.slug}),
        }

        response = self.client.post(url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_201_CREATED, response.content)
    
    def test_create_without_form(self):
        url = reverse('api:submission-list')
        data = {
            "form": None,
        }

        response = self.client.post(url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
