from unittest.mock import patch

from django.test import tag
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..base import StringValueSerializer
from ..registry import Registry
from ..validators.formats import DutchPhoneNumberValidator
from .test_registry import DjangoValidator, DRFValidator


class ValidationsAPITests(SubmissionsMixin, APITestCase):
    def setUp(self):
        self.user = StaffUserFactory()
        self.client.force_login(self.user)

        self.register = Registry()
        self.register("django")(DjangoValidator)
        self.register("drf")(DRFValidator)

        patcher = patch("openforms.validations.api.views.register", new=self.register)
        patcher.start()
        self.addCleanup(patcher.stop)

        config = GlobalConfiguration.get_solo()
        config.enable_demo_plugins = False
        config.save()

    def test_auth_required(self):
        self.client.logout()
        url = reverse("api:validators-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validations_list(self):
        with self.subTest("No query params"):
            url = reverse("api:validators-list")
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                [
                    {
                        "id": "django",
                        "label": "Django Test Validator",
                        "for_components": ["textfield"],
                    },
                    {
                        "id": "drf",
                        "label": "DRF Test Validator",
                        "for_components": ["phoneNumber"],
                    },
                ],
            )

        with self.subTest("Validators for textfield component"):
            query_params = {"component_type": "textfield"}

            response = self.client.get(reverse("api:validators-list"), query_params)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                [
                    {
                        "id": "django",
                        "label": "Django Test Validator",
                        "for_components": ["textfield"],
                    },
                ],
            )

        with self.subTest("Validators for phoneNumber component"):
            query_params = {"component_type": "phoneNumber"}

            response = self.client.get(reverse("api:validators-list"), query_params)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                [
                    {
                        "id": "drf",
                        "label": "DRF Test Validator",
                        "for_components": ["phoneNumber"],
                    },
                ],
            )

        with self.subTest("Optional query param"):
            query_params = {"component_type": ""}

            response = self.client.get(reverse("api:validators-list"), query_params)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                [
                    {
                        "id": "django",
                        "label": "Django Test Validator",
                        "for_components": ["textfield"],
                    },
                    {
                        "id": "drf",
                        "label": "DRF Test Validator",
                        "for_components": ["phoneNumber"],
                    },
                ],
            )

        with self.subTest("Invalid query params"):
            query_params = {"component_type": 123}

            response = self.client.get(reverse("api:validators-list"), query_params)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, [])

    def test_default_string_serializer(self):
        self.assertTrue(StringValueSerializer(data={"value": "foo"}).is_valid())
        self.assertTrue(StringValueSerializer(data={"value": ""}).is_valid())
        self.assertFalse(StringValueSerializer(data={"value": None}).is_valid())
        self.assertFalse(StringValueSerializer(data={"bazz": "buzz"}).is_valid())

    def test_validation_forbidden(self):
        submission = SubmissionFactory.create()
        submission_uuid = str(submission.uuid)
        url = reverse("api:validate-value", kwargs={"validator": "django"})

        response = self.client.post(
            url, {"value": "VALID", "submission_uuid": submission_uuid}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_validation(self):
        submission = SubmissionFactory.create()
        submission_uuid = str(submission.uuid)
        url = reverse("api:validate-value", kwargs={"validator": "django"})
        self._add_submission_to_session(submission)

        response = self.client.post(
            url, {"value": "VALID", "submission_uuid": submission_uuid}, format="json"
        )
        expected = {
            "is_valid": True,
            "messages": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

        response = self.client.post(
            url,
            {"value": "NOT-VALID", "submission_uuid": submission_uuid},
            format="json",
        )
        expected = {
            "is_valid": False,
            "messages": ["not VALID value"],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    @tag("gh-6751")
    def test_validation_phonenumber_with_spaces_only_value(self):
        self.register("phonenumber-nl")(DutchPhoneNumberValidator)
        submission = SubmissionFactory.create()
        submission_uuid = str(submission.uuid)
        url = reverse("api:validate-value", kwargs={"validator": "phonenumber-nl"})
        self._add_submission_to_session(submission)

        response = self.client.post(
            url,
            {"value": "      ", "submission_uuid": submission_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["isValid"], False)
