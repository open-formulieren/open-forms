from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.config.models import GlobalConfiguration
from openforms.validations.api.serializers import ValidationInputSerializer
from openforms.validations.registry import Registry
from openforms.validations.tests.test_registry import (
    DjangoValidator,
    DRFValidator,
    function_validator,
)


class ValidationsAPITests(APITestCase):
    def setUp(self):
        self.user = StaffUserFactory()
        self.client.force_login(self.user)

        register = Registry()
        register("django", verbose_name="Django Test Validator")(DjangoValidator)
        register("drf", verbose_name="DRF Test Validator")(DRFValidator)
        register("func", verbose_name="Django function Validator")(function_validator)
        register("demo", verbose_name="Demo function", is_demo_plugin=True)(
            function_validator
        )

        patcher = patch("openforms.validations.api.views.register", new=register)
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
        url = reverse("api:validators-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [
                {"id": "django", "label": "Django Test Validator"},
                {"id": "drf", "label": "DRF Test Validator"},
                {"id": "func", "label": "Django function Validator"},
            ],
        )

    def test_input_serializer(self):
        self.assertTrue(ValidationInputSerializer(data={"value": "foo"}).is_valid())
        self.assertFalse(ValidationInputSerializer(data={"value": ""}).is_valid())
        self.assertFalse(ValidationInputSerializer(data={"value": None}).is_valid())
        self.assertFalse(ValidationInputSerializer(data={"bazz": "buzz"}).is_valid())

    def test_validation(self):
        url = reverse("api:validate-value", kwargs={"validator": "django"})

        response = self.client.post(url, {"value": "VALID"}, format="json")
        expected = {
            "is_valid": True,
            "messages": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

        response = self.client.post(url, {"value": "NOT-VALID"}, format="json")
        expected = {
            "is_valid": False,
            "messages": ["not VALID value"],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)
