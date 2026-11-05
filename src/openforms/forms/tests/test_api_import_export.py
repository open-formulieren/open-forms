"""
Test the import/export interface via the API endpoints.

For detailed import/export behaviour tests, see :mod:`openforms.forms.tests.import_export`.
"""

import uuid
from io import BytesIO
from unittest.mock import ANY, patch
from zipfile import ZipFile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import factory
import factory.fuzzy
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import TokenFactory, UserFactory
from openforms.config.tests.factories import (
    ThemeFactory,
)
from openforms.forms.import_export.service import (
    FormExportOptions,
    FormImportOptions,
)

from ..import_export.service import (
    AdditionalFormConfigurationOptions,
    Artifact,
    FormConfigurationOptions,
)
from ..models import Form
from .factories import (
    CategoryFactory,
    FormFactory,
)


class ExportAPIAccessControlTests(APITestCase):
    def test_form_export_authenticated_user_required(self):
        form, _ = FormFactory.create_batch(2)

        url = reverse("api:form-export", args=(form.uuid,))
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_session_auth_not_allowed(self):
        user = UserFactory.create(is_staff=True, user_permissions=["forms.change_form"])
        self.client.login(
            request=HttpRequest(), username=user.username, password="secret"
        )
        form = FormFactory.create()
        url = reverse("api:form-export", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_export_staff_required(self):
        user = UserFactory.create(
            is_staff=False, user_permissions=["forms.change_form"]
        )
        token = TokenFactory(user=user)
        form = FormFactory.create()
        url = reverse("api:form-export", args=(form.uuid,))

        response = self.client.post(
            url, headers={"Authorization": f"Token {token.key}"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FuzzyExportOptionsFactory(factory.DictFactory):
    removeSensitiveContent = factory.fuzzy.FuzzyChoice([True, False])
    formConfiguration = factory.List(
        [factory.fuzzy.FuzzyChoice(FormConfigurationOptions, getter=lambda o: o.value)],
    )
    additionalFormConfiguration = factory.List(
        [
            factory.fuzzy.FuzzyChoice(
                AdditionalFormConfigurationOptions, getter=lambda o: o.value
            )
        ],
    )


class FunctionalExportAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        token = TokenFactory.create(
            user__is_staff=True,
            user__user_permissions=["forms.change_form"],
        )
        cls.auth_headers = {"Authorization": f"Token {token.key}"}

    def test_export_without_any_options_produces_export_zip(self):
        form = FormFactory.create()
        url = reverse("api:form-export", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.post(url, headers=self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["content-type"], "application/zip")
        zf = ZipFile(BytesIO(response.content))
        self.assertEqual(
            set(zf.namelist()),
            {
                "forms.json",
                "formSteps.json",
                "formDefinitions.json",
                "formLogic.json",
                "formVariables.json",
                "_meta.json",
            },
        )

    def test_invalid_export_options_shape_returns_error_response(self):
        form = FormFactory.create()
        url = reverse("api:form-export", kwargs={"uuid_or_slug": form.uuid})

        response = self.client.post(
            url,
            data={"removeSensitiveContent": "wrong-type"},
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        error = response_data["invalidParams"][0]
        self.assertEqual(error["name"], "removeSensitiveContent")
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(error["reason"], _("Must be a valid boolean."))

    def test_export_options_are_forwarded_to_export_function(self):
        form = FormFactory.create()
        url = reverse("api:form-export", kwargs={"uuid_or_slug": form.uuid})
        options = FuzzyExportOptionsFactory.build()

        with patch("openforms.forms.api.viewsets.export_form") as mock_export_form:
            response = self.client.post(url, data=options, headers=self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_export_form.assert_called_once_with(
            form.id,
            response=ANY,
            export_options=FormExportOptions(
                remove_sensitive_content=options["removeSensitiveContent"],
                form_configuration=options["formConfiguration"],
                additional_form_configuration=options["additionalFormConfiguration"],
            ),
        )


class ImportAPIAccessControlTests(APITestCase):
    def test_form_import_authenticated_user_required(self):
        url = reverse("api:forms-import")

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_session_auth_not_allowed(self):
        user = UserFactory.create(is_staff=True, user_permissions=["forms.change_form"])
        self.client.login(
            request=HttpRequest(), username=user.username, password="secret"
        )
        url = reverse("api:forms-import")

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_import_staff_required(self):
        user = UserFactory.create(
            is_staff=False, user_permissions=["forms.change_form"]
        )
        token = TokenFactory(user=user)
        url = reverse("api:forms-import")

        response = self.client.post(
            url, headers={"Authorization": f"Token {token.key}"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FunctionalImportAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        token = TokenFactory.create(
            user__is_staff=True,
            user__user_permissions=["forms.change_form"],
        )
        cls.auth_headers = {"Authorization": f"Token {token.key}"}

    def test_import_without_any_options_imports_form_from_zip(self):
        artifact = Artifact(
            forms=[
                {
                    "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                    "name": "Import form",
                    "slug": "import-form",
                    "product": None,
                }
            ],
        )
        export_file = SimpleUploadedFile(
            "file.zip", b"", content_type="application/zip"
        )
        artifact.write_zip(export_file)
        export_file.seek(0)
        url = reverse("api:forms-import")

        response = self.client.post(
            url,
            {"file": export_file},
            format="multipart",
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        imported_form = Form.objects.get()
        self.assertEqual(imported_form.name, "Import form")
        self.assertNotEqual(
            str(imported_form.uuid), "b8315e1d-3134-476f-8786-7661d8237c51"
        )
        self.assertEqual(response.json()["uuid"], str(imported_form.uuid))

    def test_import_options_are_forwarded_to_import_function(self):
        artifact = Artifact(
            forms=[
                {
                    "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                    "name": "Import form",
                    "slug": "import-form",
                    "product": None,
                }
            ],
        )
        export_file = SimpleUploadedFile(
            "file.zip", b"", content_type="application/zip"
        )
        artifact.write_zip(export_file)
        export_file.seek(0)
        url = reverse("api:forms-import")

        with patch(
            "openforms.forms.api.viewsets.import_form",
            return_value=Form(uuid=uuid.uuid4()),
        ) as mock_import_form:
            response = self.client.post(
                url,
                {
                    "file": export_file,
                    # a subset of options, arbitrarily chosen
                    "formConfiguration": [
                        FormConfigurationOptions.auth_backends,
                        FormConfigurationOptions.prefill,
                    ],
                    "additionalFormConfiguration": [
                        AdditionalFormConfigurationOptions.product,
                    ],
                },
                format="multipart",
                headers=self.auth_headers,
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_import_form.assert_called_once_with(
            ANY,
            FormImportOptions(
                form_configuration=[
                    FormConfigurationOptions.auth_backends,
                    FormConfigurationOptions.prefill,
                ],
                additional_form_configuration=[
                    AdditionalFormConfigurationOptions.product,
                ],
                category=None,
                theme=None,
            ),
        )

    def test_import_with_explicit_theme_and_category(self):
        theme = ThemeFactory.create()
        category = CategoryFactory.create()
        artifact = Artifact(
            forms=[
                {
                    "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                    "name": "Import form",
                    "slug": "import-form",
                    "product": None,
                }
            ],
        )
        export_file = SimpleUploadedFile(
            "file.zip", b"", content_type="application/zip"
        )
        artifact.write_zip(export_file)
        export_file.seek(0)
        url = reverse("api:forms-import")

        response = self.client.post(
            url,
            {
                "file": export_file,
                "theme": theme.uuid,
                "category": category.uuid,
            },
            format="multipart",
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        imported_form = Form.objects.get()
        self.assertEqual(imported_form.theme, theme)
        self.assertEqual(imported_form.category, category)
