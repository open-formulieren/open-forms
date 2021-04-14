import json
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

        url = reverse("api:form-list")
        response = self.client.get(url, format="json", secure=True)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list(self):
        FormFactory.create_batch(2)

        url = reverse("api:form-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

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
        self.assertEqual(imported_form.backend, form1.backend)
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

        self.assertEqual(response.data["error"].code, "invalid")

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
