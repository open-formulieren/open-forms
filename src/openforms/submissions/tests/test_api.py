from unittest import expectedFailure

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory

from .factories import SubmissionFactory

# Old submissions API - some concepts may still be relevant, others aren't.
# TODO: revisit these tests after the submissions api rework is completed


@expectedFailure
class SubmissionAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        self.client.login(
            request=HttpRequest(), username=user.username, password="secret"
        )

    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()

        url = reverse("api:submission-list")
        response = self.client.get(url, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        form = FormFactory.create()
        SubmissionFactory.create(form=form)

        url = reverse("api:submission-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class RemovalMethodsAPITests(APITestCase):
    def test_get_removal_methods_returns_correct_removal_methods(self):
        url = reverse("api:submissions:removal-methods")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                ["delete_permanently", "Submissions will be deleted"],
                [
                    "make_anonymous",
                    "Sensitive data within the submissions will be deleted",
                ],
            ],
        )
