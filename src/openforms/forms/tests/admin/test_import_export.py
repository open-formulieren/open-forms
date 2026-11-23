import json
from io import BytesIO
from unittest.mock import ANY, patch
from zipfile import ZipFile

from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

import factory
import factory.fuzzy
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.config.tests.factories import (
    ThemeFactory,
)
from openforms.forms.import_export.datastructures import (
    FormExportOptions,
    FormImportOptions,
)

from ...import_export.service import (
    AdditionalFormConfigurationOptions,
    Artifact,
    FormConfigurationOptions,
)
from ...models import Form
from ...tests.factories import FormFactory
from ..factories import (
    CategoryFactory,
)


class FuzzyExportOptionsFactory(factory.DictFactory):
    remove_sensitive_content = factory.fuzzy.FuzzyChoice([True, False])
    form_configuration = factory.List(
        [factory.fuzzy.FuzzyChoice(FormConfigurationOptions, getter=lambda o: o.value)],
    )
    additional_form_configuration = factory.List(
        [
            factory.fuzzy.FuzzyChoice(
                AdditionalFormConfigurationOptions, getter=lambda o: o.value
            )
        ],
    )


@disable_admin_mfa()
class FormAdminExportTests(ParametrizedTestCase, TestCase):
    """
    Test the admin wrapper around the export functionality.

    For detailed export tests, see the dedicated test modules. Tests here focus on the
    integration into the admin of the public export interface.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_form_admin_export_without_any_options_produces_export_zip(self):
        form = FormFactory.create(
            authentication_backend="digid",
            authentication_backend_options={
                "loa": DIGID_DEFAULT_LOA,
            },
        )
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(admin_url, data={"_export": "Export"})

        self.assertEqual(response.status_code, 200)
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

    @parametrize(
        ("options_json", "expect_error"),
        [
            (
                json.dumps(
                    {"unknown-option": True, "another-unknown-option": "some-value"}
                ),
                False,
            ),
            (
                # The value of the "remove_sensitive_content" option should be a boolean
                json.dumps({"remove_sensitive_content": "some unexpected value"}),
                True,
            ),
            (
                '{"broken',
                True,
            ),
        ],
    )
    @override_settings(LANGUAGE_CODE="en")
    def test_malformed_export_options_json_output(
        self, options_json: str, expect_error: bool
    ):
        """
        Test that malformed export options are either ignored or reported to the user.
        """
        form = FormFactory.create()
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))

        response = self.client.post(
            admin_url,
            data={"_export": "Export", "export_options": options_json},
        )

        match expect_error:
            case True:
                self.assertEqual(response.status_code, 302)
                # follow the redirect
                _response = self.client.get(response["Location"])
                self.assertContains(
                    _response,
                    f"Something went wrong while exporting form {form}",
                )
            case False:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["content-type"], "application/zip")

    def test_form_admin_export_options_are_translated_to_form_export_options(self):
        form = FormFactory.create()
        admin_url = reverse("admin:forms_form_change", args=(form.pk,))
        export_options = FuzzyExportOptionsFactory.build()
        post_data = {
            "_export": "Export",
            "export_options": json.dumps(export_options),
        }

        with patch("openforms.forms.admin.form.export_form") as mock_export_form:
            response = self.client.post(admin_url, data=post_data)

        self.assertEqual(response.status_code, 200)
        mock_export_form.assert_called_once_with(
            ANY,
            response=ANY,
            export_options=FormExportOptions(
                remove_sensitive_content=export_options["remove_sensitive_content"],
                form_configuration=export_options["form_configuration"],
                additional_form_configuration=export_options[
                    "additional_form_configuration"
                ],
            ),
        )


@disable_admin_mfa()
class FormAdminImportTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_form_admin_import_requires_staff_user_with_form_add_permissions(self):
        url = reverse("admin:forms_import")

        with self.subTest("anonymous_user"):
            response = self.app.get(url, user=None)

            self.assertRedirects(
                response,  # pyright: ignore[reportArgumentType]
                f"{reverse('admin:login')}?next={url}",
                fetch_redirect_response=False,
            )

        with self.subTest("non-staff user"):
            user = UserFactory.create(
                is_staff=False, user_permissions=["forms.add_form"]
            )

            response = self.app.get(url, user=user)

            self.assertRedirects(
                response,  # pyright: ignore[reportArgumentType]
                f"{reverse('admin:login')}?next={url}",
                fetch_redirect_response=False,
            )

        with self.subTest("staff user missing required permissions"):
            user = UserFactory.create(is_staff=True, user_permissions=[])

            response = self.app.get(url, user=user, status=403)

        with self.subTest("staff user with required permission"):
            user = UserFactory.create(
                is_staff=True, user_permissions=["forms.add_form"]
            )

            response = self.app.get(url, user=user)

            self.assertEqual(response.status_code, 200)

    @override_settings(LANGUAGE_CODE="en")
    def test_form_admin_import_button(self):
        response = self.app.get(reverse("admin:forms_form_changelist"), user=self.user)

        response = response.click(href=reverse("admin:forms_import"))

        self.assertEqual(response.status_code, 200)

        # Page should have the import form
        self.assertIn("file", response.form.fields)

    def test_form_admin_import_single_export_file_is_imported_synchronously(self):
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
        export_file = BytesIO()
        artifact.write_zip(export_file)
        import_page = self.app.get(reverse("admin:forms_import"), user=self.user)

        html_form = import_page.form
        html_form["file"] = ("file.zip", export_file.getvalue())
        response = html_form.submit("_import")

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))  # pyright: ignore[reportArgumentType]
        self.assertEqual(Form.objects.count(), 1)
        imported_form = Form.objects.get()
        self.assertNotEqual(imported_form.uuid, "b8315e1d-3134-476f-8786-7661d8237c51")
        self.assertEqual(imported_form.name, "Import form")

        response = response.follow()
        self.assertContains(
            response,  # pyright: ignore[reportArgumentType]
            _("Form successfully imported!"),
        )

    def test_form_admin_import_invalid_import_data_reports_generic_error(self):
        artifact = Artifact(forms=[{"wrong": "fields"}])
        export_file = BytesIO()
        artifact.write_zip(export_file)
        import_page = self.app.get(reverse("admin:forms_import"), user=self.user)

        html_form = import_page.form
        html_form["file"] = ("file.zip", export_file.getvalue())
        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,  # pyright: ignore[reportArgumentType]
            _("Something went wrong while importing form: {}").format(""),
        )

    @tag("gh-2851")
    def test_form_admin_import_with_english_browser_locale_does_not_mess_up_dutch_name(
        self,
    ):
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
        export_file = BytesIO()
        artifact.write_zip(export_file)
        import_page = self.app.get(
            reverse("admin:forms_import"),
            user=self.user,
            headers={"Accept-Language": "en"},
        )

        html_form = import_page.form
        html_form["file"] = ("file.zip", export_file.getvalue())
        response = html_form.submit("_import", headers={"Accept-Language": "en"})

        self.assertEqual(response.status_code, 302)
        form = Form.objects.get(slug="import-form")
        self.assertEqual(form.name_nl, "Import form")
        self.assertIsNone(form.name_en)

    def test_form_admin_import_options_are_translated_to_form_import_options(self):
        # contents are irrelevant since we mock the import call anyway
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
        export_file = BytesIO()
        artifact.write_zip(export_file)
        response = self.app.get(reverse("admin:forms_import"), user=self.user)
        html_form = response.form
        html_form["file"] = ("file.zip", export_file.getvalue())

        # a subset of options, arbitrarily chosen
        html_form["form_configuration"] = [
            FormConfigurationOptions.auth_backends,
            FormConfigurationOptions.prefill,
        ]
        html_form["additional_form_configuration"] = [
            AdditionalFormConfigurationOptions.product,
        ]
        with patch("openforms.forms.admin.views.import_form") as mock_import_form:
            response = html_form.submit("_import")

        mock_import_form.assert_called_once_with(
            ANY,
            FormImportOptions(
                form_configuration=[
                    FormConfigurationOptions.prefill,
                    FormConfigurationOptions.auth_backends,
                ],
                additional_form_configuration=[
                    AdditionalFormConfigurationOptions.product,
                ],
                category=None,
                theme=None,
            ),
        )

    def test_form_admin_import_with_theme_and_category(self):
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
        export_file = BytesIO()
        artifact.write_zip(export_file)
        response = self.app.get(reverse("admin:forms_import"), user=self.user)
        html_form = response.form
        html_form["file"] = ("file.zip", export_file.getvalue())
        # Set the ID's of the theme and category defined above
        html_form["theme"] = str(theme.uuid)
        html_form["category"] = str(category.uuid)

        response = html_form.submit("_import")

        self.assertEqual(response.status_code, 302)
        form = Form.objects.get()
        self.assertEqual(form.theme, theme)
        self.assertEqual(form.category, category)
