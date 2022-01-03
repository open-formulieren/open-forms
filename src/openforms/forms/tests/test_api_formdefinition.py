from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.prefill.models import PrefillConfig

from ..models import FormDefinition
from .factories import FormDefinitionFactory, FormStepFactory


class FormDefinitionsAPITests(APITestCase):
    def test_list_anon(self):
        FormDefinitionFactory.create_batch(2)

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        FormDefinitionFactory.create_batch(2)

        url = reverse("api:formdefinition-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_permission_cant_update(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        data = {
            "name": "Updated name",
            "slug": "updated-slug",
            "configuration": {
                "display": "form",
                "components": [{"label": "Existing field"}, {"label": "New field"}],
            },
        }
        with self.subTest("user"):
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("permissions"):
            user.is_staff = True
            user.save()
            response = self.client.patch(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_without_permission_cant_create(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        url = reverse("api:formdefinition-list")
        data = {
            "name": "Name",
            "slug": "a-slug",
            "configuration": {
                "display": "form",
                "components": [{"label": "New field"}],
            },
        }
        with self.subTest("user"):
            response = self.client.post(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.post(url, data=data)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_without_permission_cant_delete(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )
        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})

        with self.subTest("user"):
            response = self.client.delete(url)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        with self.subTest("staff"):
            user.is_staff = True
            user.save()
            response = self.client.delete(url)
            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_update(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            login_required=False,
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.patch(
            url,
            data={
                "name": "Updated name",
                "slug": "updated-slug",
                "configuration": {
                    "display": "form",
                    "components": [{"label": "Existing field"}, {"label": "New field"}],
                },
                "login_required": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        definition.refresh_from_db()

        self.assertEqual("Updated name", definition.name)
        self.assertEqual("updated-slug", definition.slug)
        self.assertEqual(True, definition.login_required)
        self.assertIn({"label": "New field"}, definition.configuration["components"])

    def test_create(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "display": "form",
                    "components": [{"label": "New field"}],
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        definition = FormDefinition.objects.get()

        self.assertEqual("Name", definition.name)
        self.assertEqual("a-slug", definition.slug)
        self.assertEqual(
            [{"label": "New field"}], definition.configuration["components"]
        )

    def test_create_no_camelcase_snakecase_conversion(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        url = reverse("api:formdefinition-list")
        response = self.client.post(
            url,
            data={
                "name": "Name",
                "slug": "a-slug",
                "configuration": {
                    "someCamelCase": "field",
                },
            },
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        config = FormDefinition.objects.get().configuration
        self.assertIn("someCamelCase", config)
        self.assertNotIn("some_amel_case", config)

    def test_delete(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        definition = FormDefinitionFactory.create(
            name="test form definition",
            slug="test-form-definition",
            configuration={
                "display": "form",
                "components": [{"label": "Existing field"}],
            },
        )

        url = reverse("api:formdefinition-detail", kwargs={"uuid": definition.uuid})
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        self.assertEqual(0, FormDefinition.objects.all().count())

    def test_used_in_forms_serializer_field(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        form_step = FormStepFactory.create()
        url = reverse(
            "api:formdefinition-detail", args=(form_step.form_definition.uuid,)
        )
        form_url = reverse("api:form-detail", args=(form_step.form.uuid,))

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data["usedIn"]), 1)
        self.assertEqual(
            response_data["usedIn"][0]["url"], f"http://testserver{form_url}"
        )


class FormioCoSignComponentValidationTests(APITestCase):
    """
    Test specific Formio component type validations for form definitions.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_configuration_with_co_sign_but_missing_auth_plugin(self):
        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "label": "Co-sign test",
                }
            ]
        }

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["name"], "configuration")

    def test_configuration_with_co_sign_but_missing_global_config(self):
        prefill_config = PrefillConfig.get_solo()
        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "label": "Co-sign test",
                    "authPlugin": "digid",
                }
            ]
        }
        with self.subTest("assert test data as expected"):
            self.assertEqual(prefill_config.default_person_plugin, "")
            self.assertEqual(prefill_config.default_company_plugin, "")

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["name"], "configuration")

    @patch("openforms.prefill.co_sign.PrefillConfig.get_solo")
    def test_configuration_with_co_sign_ok(self, mock_get_solo):
        mock_get_solo.return_value = PrefillConfig(default_person_plugin="stufbg")

        url = reverse("api:formdefinition-list")
        config = {
            "components": [
                {
                    "type": "coSign",
                    "label": "Co-sign test",
                    "authPlugin": "digid",
                }
            ]
        }

        response = self.client.post(
            url,
            data={
                "name": "Some name",
                "slug": "some-slug",
                "configuration": config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
