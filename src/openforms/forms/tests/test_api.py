import uuid
from unittest import expectedFailure

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Form, FormStep
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

    def test_create_form_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 1)
        form = Form.objects.get()
        self.assertEqual(form.name, "Test Post Form")
        self.assertEqual(form.slug, "test-post-form")

    def test_create_form_unsuccessful_with_bad_data(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-list")
        data = {
            "bad": "data",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Form.objects.exists())
        self.assertEqual(
            response.json(),
            {"name": ["Dit veld is vereist."], "slug": ["Dit veld is vereist."]},
        )

    def test_create_form_unsuccessful_without_authorization(self):
        url = reverse("api:form-list")
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Form.objects.exists())

    def test_partial_update_of_form(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Patch Form")

    def test_partial_update_of_form_unsuccessful_without_authorization(self):
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Patch Form")

    def test_partial_update_of_form_unsuccessful_when_form_cannot_be_found(self):
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid": uuid.uuid4()})
        data = {
            "name": "Test Patch Form",
        }
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_update_of_form_successful(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "name": "Test Put Form",
            "slug": "test-put-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form.refresh_from_db()
        self.assertEqual(form.name, "Test Put Form")
        self.assertEqual(form.slug, "test-put-form")

    def test_complete_update_of_form_with_incomplete_data_unsuccessful(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "name": "Test Put Form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"slug": ["Dit veld is vereist."]})

    def test_complete_update_of_form_unsuccessful_without_authorization(self):
        form = FormFactory.create()
        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        form.refresh_from_db()
        self.assertNotEqual(form.name, "Test Put Form")
        self.assertNotEqual(form.slug, "test-put-form")

    def test_complete_update_of_form_unsuccessful_with_bad_data(self):
        form = FormFactory.create()
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-detail", kwargs={"uuid": form.uuid})
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"name": ["Dit veld is vereist."], "slug": ["Dit veld is vereist."]},
        )

    def test_complete_update_of_form_when_form_cannot_be_found(self):
        self.user.is_staff = True
        self.user.save()

        url = reverse("api:form-detail", kwargs={"uuid": uuid.uuid4()})
        data = {
            "name": "Test Post Form",
            "slug": "test-post-form",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FormsStepsAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.step = FormStepFactory.create()
        self.other_form_definition = FormDefinitionFactory.create()

        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        assert self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

    def test_steps_list(self):
        url = reverse("api:form-steps-list", kwargs={"form_uuid": self.step.form.uuid})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_create_form_step_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-steps-list", kwargs={"form_uuid": self.step.form.uuid})
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_create_form_step_unsuccessful_with_bad_data(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-steps-list", kwargs={"form_uuid": self.step.form.uuid})
        data = {
            "bad": "data",
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FormStep.objects.count(), 1)
        self.assertEqual(response.json(), {"formDefinition": ["Dit veld is vereist."]})

    def test_create_form_step_unsuccessful_when_form_is_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse("api:form-steps-list", kwargs={"form_uuid": uuid.uuid4()})
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_create_form_step_unsuccessful_without_authorization(self):
        url = reverse("api:form-steps-list", kwargs={"form_uuid": self.step.form.uuid})
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_complete_form_step_update_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_complete_form_step_update_unsuccessful_when_form_step_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_complete_form_step_update_unsuccessful_with_non_existant_form_definition(
        self,
    ):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": uuid.uuid4()},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )
        self.assertEqual(
            response.json(),
            {"formDefinition": ["Ongeldige hyperlink - Object bestaat niet."]},
        )

    def test_complete_form_step_update_unsuccessful_with_bad_data(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        data = {
            "bad": "data",
        }
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(FormStep.objects.count(), 1)
        self.assertEqual(response.json(), {"formDefinition": ["Dit veld is vereist."]})

    def test_complete_form_step_update_unsuccessful_without_authorization(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_partial_form_step_update_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": self.other_form_definition.uuid},
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            FormStep.objects.filter(form_definition=self.other_form_definition).count(),
            1,
        )

    def test_partial_form_step_update_unsuccessful_when_form_step_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": uuid.uuid4()}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_partial_form_step_update_unsuccessful_when_form_definition_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": uuid.uuid4()}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )
        self.assertEqual(
            response.json(),
            {"formDefinition": ["Ongeldige hyperlink - Object bestaat niet."]},
        )

    def test_partial_form_step_update_unsuccessful_without_authorization(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        form_detail_url = reverse(
            "api:formdefinition-detail", kwargs={"uuid": self.step.form_definition.uuid}
        )
        data = {"formDefinition": f"http://testserver{form_detail_url}"}
        response = self.client.patch(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            FormStep.objects.filter(form_definition=self.other_form_definition).exists()
        )

    def test_delete_form_step_successful(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FormStep.objects.exists())

    def test_delete_form_step_unsuccessful_when_form_not_found(self):
        self.user.is_staff = True
        self.user.save()
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": uuid.uuid4()},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(FormStep.objects.count(), 1)

    def test_delete_form_step_unsuccessful_when_not_authenticated(self):
        url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": self.step.form.uuid, "uuid": self.step.uuid},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(FormStep.objects.count(), 1)


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
