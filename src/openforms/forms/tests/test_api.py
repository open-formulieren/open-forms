import json
import uuid
from io import BytesIO
from unittest import expectedFailure
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import TokenFactory

from ..models import Form, FormDefinition, FormStep
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

    def test_delete_form_step_unsuccessful_when_not_authorized(self):
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


class ImportExportAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.token = TokenFactory(user=self.user)

    def test_form_export(self):
        self.user.is_staff = True
        self.user.save()

        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        form_step, _ = FormStepFactory.create_batch(2)
        form_step.form = form
        form_step.form_definition = form_definition
        form_step.save()

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(), ["forms.json", "formSteps.json", "formDefinitions.json"]
        )

        forms = json.loads(zf.read("forms.json"))
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]["uuid"], str(form.uuid))
        self.assertEqual(forms[0]["name"], form.name)
        self.assertEqual(forms[0]["slug"], form.slug)
        self.assertEqual(len(forms[0]["steps"]), form.formstep_set.count())
        self.assertIsNone(forms[0]["product"])

        form_definitions = json.loads(zf.read("formDefinitions.json"))
        self.assertEqual(len(form_definitions), 1)
        self.assertEqual(form_definitions[0]["uuid"], str(form_definition.uuid))
        self.assertEqual(form_definitions[0]["name"], form_definition.name)
        self.assertEqual(form_definitions[0]["slug"], form_definition.slug)
        self.assertEqual(
            form_definitions[0]["configuration"],
            form_definition.configuration,
        )

        form_steps = json.loads(zf.read("formSteps.json"))
        self.assertEqual(len(form_steps), 1)
        self.assertEqual(form_steps[0]["configuration"], form_definition.configuration)

    def test_form_export_token_auth_required(self):
        form, _ = FormFactory.create_batch(2)

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        form, _ = FormFactory.create_batch(2)

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        form_step, _ = FormStepFactory.create_batch(2)
        form_step.form = form
        form_step.form_definition = form_definition
        form_step.save()

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_import(self):
        self.user.is_staff = True
        self.user.save()

        form1, form2 = FormFactory.create_batch(2)
        form_definition1, form_definition2 = FormDefinitionFactory.create_batch(2)
        form_step1 = FormStepFactory.create(
            form=form1, form_definition=form_definition1
        )
        FormStepFactory.create(form=form2, form_definition=form_definition2)

        url = reverse("api:form-export", args=(form1.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form1.delete()
        form_definition1.delete()
        form_step1.delete()

        f = SimpleUploadedFile(
            "file.zip", response.content, content_type="application/zip"
        )
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)

        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.first()
        imported_form_definition = imported_form_step.form_definition

        self.assertNotEqual(imported_form.pk, form1.pk)
        self.assertNotEqual(imported_form.uuid, str(form1.uuid))
        self.assertEqual(imported_form.active, False)
        self.assertEqual(imported_form.registration_backend, form1.registration_backend)
        self.assertEqual(imported_form.name, form1.name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, form1.slug)

        self.assertNotEqual(imported_form_definition.pk, form_definition1.pk)
        self.assertNotEqual(imported_form_definition.uuid, str(form_definition1.uuid))
        self.assertEqual(
            imported_form_definition.configuration, form_definition1.configuration
        )
        self.assertEqual(
            imported_form_definition.login_required, form_definition1.login_required
        )
        self.assertEqual(imported_form_definition.name, form_definition1.name)
        self.assertEqual(imported_form_definition.slug, form_definition1.slug)

        self.assertNotEqual(imported_form_step.pk, form_step1.pk)
        self.assertNotEqual(imported_form_step.uuid, str(form_step1.uuid))
        self.assertEqual(
            imported_form_step.availability_strategy, form_step1.availability_strategy
        )
        self.assertEqual(imported_form_step.form.pk, imported_form.pk)
        self.assertEqual(
            imported_form_step.form_definition.pk, imported_form_definition.pk
        )
        self.assertEqual(imported_form_step.optional, form_step1.optional)
        self.assertEqual(imported_form_step.order, form_step1.order)

    def test_form_import_error_slug_already_exists(self):
        self.user.is_staff = True
        self.user.save()

        form1, form2 = FormFactory.create_batch(2)
        form_definition1, form_definition2 = FormDefinitionFactory.create_batch(2)
        FormStepFactory.create(form=form1, form_definition=form_definition1)
        FormStepFactory.create(form=form2, form_definition=form_definition2)

        url = reverse("api:form-export", args=(form1.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        f = SimpleUploadedFile(
            "file.zip", response.content, content_type="application/zip"
        )
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": f},
            format="multipart",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data["non_field_errors"].code, "invalid")

    def test_form_import_token_auth_required(self):
        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": b""},
            format="multipart",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file": b""},
            format="multipart",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        url = reverse("api:forms-import")
        response = self.client.post(
            url,
            {"file", b""},
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
            HTTP_CONTENT_DISPOSITION="attachment;filename=file.zip",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CopyFormAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.token = TokenFactory(user=self.user)

    def test_form_copy(self):
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        copied_form = Form.objects.last()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["uuid"], str(copied_form.uuid))
        self.assertEqual(response.json()["name"], copied_form.name)
        self.assertEqual(response.json()["loginRequired"], copied_form.login_required)
        self.assertEqual(response.json()["product"], copied_form.product)
        self.assertEqual(response.json()["slug"], copied_form.slug)
        self.assertEqual(
            response.json()["steps"][0]["uuid"], str(copied_form_step.uuid)
        )
        self.assertEqual(
            response.json()["steps"][0]["formDefinition"],
            copied_form_step.form_definition.name,
        )

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertIn(
            reverse("api:form-detail", kwargs={"uuid": copied_form.uuid}),
            response["Location"],
        )

        self.assertNotEqual(copied_form.pk, form.pk)
        self.assertNotEqual(copied_form.uuid, str(form.uuid))
        self.assertEqual(copied_form.active, form.active)
        self.assertEqual(copied_form.registration_backend, form.registration_backend)
        self.assertEqual(copied_form.name, f"{form.name} (kopie)")
        self.assertIsNone(copied_form.product)
        self.assertEqual(copied_form.slug, f"{form.slug}-kopie")

        self.assertNotEqual(copied_form_step.pk, form_step.pk)
        self.assertNotEqual(copied_form_step.uuid, str(form_step.uuid))
        self.assertEqual(
            copied_form_step.availability_strategy, form_step.availability_strategy
        )
        self.assertEqual(copied_form_step.form.pk, copied_form.pk)
        self.assertEqual(copied_form_step.optional, form_step.optional)
        self.assertEqual(copied_form_step.order, form_step.order)

    def test_form_copy_already_exists(self):
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["name"], f"{form.name} (kopie)")
        self.assertEqual(response.json()["slug"], f"{form.slug}-kopie")

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["name"], f"{form.name} (kopie)")
        self.assertEqual(response.json()["slug"], f"{form.slug}-kopie-2")

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["name"], f"{form.name} (kopie)")
        self.assertEqual(response.json()["slug"], f"{form.slug}-kopie-3")

    def test_form_copy_token_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid": form.uuid})
        response = self.client.post(
            url,
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
