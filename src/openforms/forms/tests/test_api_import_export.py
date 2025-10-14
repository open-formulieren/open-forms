import json
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import TokenFactory, UserFactory
from openforms.variables.constants import FormVariableSources

from ...emails.tests.factories import ConfirmationEmailTemplateFactory
from ..constants import EXPORT_META_KEY
from ..models import Form, FormDefinition, FormStep
from .factories import (
    FormDefinitionFactory,
    FormFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)


class ImportExportAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.token = TokenFactory(user=self.user)

    def test_form_export(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form, _ = FormFactory.create_batch(2)
        form_definition, _ = FormDefinitionFactory.create_batch(2)
        # This creates one form variable for the component in the default definition
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormStepFactory.create()
        FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test-user-defined"
        )

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            zf.namelist(),
            [
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                f"{EXPORT_META_KEY}.json",
            ],
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

        form_variables = json.loads(zf.read("formVariables.json"))
        # Only user defined form variables are included in the export
        self.assertEqual(len(form_variables), 1)
        self.assertEqual(FormVariableSources.user_defined, form_variables[0]["source"])

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
        # export, delete, import roundtrip
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form1 = FormFactory.create(send_confirmation_email=True)
        original_registration_backends = form1.registration_backends.order_by("id")
        form2 = FormFactory.create()
        FormRegistrationBackendFactory.create_batch(2, form=form1, backend="demo")
        form_definition1, form_definition2 = FormDefinitionFactory.create_batch(2)
        form_step1 = FormStepFactory.create(
            form=form1, form_definition=form_definition1
        )
        FormStepFactory.create(form=form2, form_definition=form_definition2)

        email_tpl = ConfirmationEmailTemplateFactory.create(form=form1, with_tags=True)

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)

        form_uuid = response.json()["uuid"]
        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.first()
        imported_form_definition = imported_form_step.form_definition

        self.assertEqual(form_uuid, str(imported_form.uuid))
        self.assertNotEqual(imported_form.pk, form1.pk)
        self.assertNotEqual(imported_form.uuid, str(form1.uuid))
        self.assertEqual(imported_form.active, False)
        for imported, original in zip(
            imported_form.registration_backends.order_by("id"),
            original_registration_backends,
            strict=False,
        ):
            self.assertEqual(imported.key, original.key)
            self.assertEqual(imported.name, original.name)
            self.assertEqual(imported.backend, original.backend)
            self.assertEqual(imported.options, original.options)
        self.assertEqual(imported_form.name, form1.name)
        self.assertIsNone(imported_form.product)
        self.assertEqual(imported_form.slug, form1.slug)

        self.assertEqual(
            imported_form.confirmation_email_template.content, email_tpl.content
        )
        self.assertEqual(
            imported_form.confirmation_email_template.subject, email_tpl.subject
        )

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
        self.assertEqual(imported_form_step.form.pk, imported_form.pk)
        self.assertEqual(
            imported_form_step.form_definition.pk, imported_form_definition.pk
        )
        self.assertEqual(imported_form_step.order, form_step1.order)

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_form_import_form_slug_already_exists(self, _mock):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form1 = FormFactory.create(slug="my-slug")
        form_definition1 = FormDefinitionFactory.create(is_reusable=True)
        FormStepFactory.create(form=form1, form_definition=form_definition1)

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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        form_uuid = response.json()["uuid"]
        imported_form = Form.objects.last()
        imported_form_step = imported_form.formstep_set.first()
        imported_form_definition = imported_form_step.form_definition

        # Check that the return response's uuid is the same as the last form in the db
        self.assertEqual(form_uuid, str(imported_form.uuid))
        # check we imported a new form
        self.assertNotEqual(form1.pk, imported_form.pk)
        # check we added random hex chars
        self.assertRegex(imported_form.slug, r"^my-slug-[0-9a-f]{6}$")
        # check uuid mapping still works
        self.assertEqual(imported_form_definition.uuid, form_definition1.uuid)

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
