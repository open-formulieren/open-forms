import zipfile
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

import time_machine
from privates.storages import private_media_storage
from privates.test import temp_private_root
from rest_framework.exceptions import ValidationError

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as YIVI_OIDC_PLUGIN_ID,
)
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.config.tests.factories import ThemeFactory
from openforms.logging.models import TimelineLogProxy
from openforms.products.tests.factories import ProductFactory
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import process_forms_export, process_forms_import
from ...import_export.constants import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
)
from ...models.form import Form, FormsExport
from ..factories import CategoryFactory, FormFactory


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class ExportFormsTaskTests(TestCase):
    @time_machine.travel("2022-02-21T00:00:00", tick=False)
    def test_zip_file_contains_data(self):
        form1, form2 = FormFactory.create_batch(2)
        user = SuperUserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
            export_options={},
        )

        # Test that the forms export model was created with the right data
        forms_exports = FormsExport.objects.all()

        self.assertEqual(1, forms_exports.count())

        forms_export = forms_exports.get()

        self.assertEqual(forms_export.datetime_requested, timezone.now())
        self.assertEqual(user, forms_export.user)

        # Test that the zip file contains the right forms
        with (
            forms_export.export_content.open("rb") as content,
            zipfile.ZipFile(content, "r") as file,
        ):
            names_list = file.namelist()

        self.assertEqual(2, len(names_list))
        self.assertIn(f"form_{form1.slug}.zip", names_list)
        self.assertIn(f"form_{form2.slug}.zip", names_list)

        # Test that the email has been sent to the user
        sent_mail = mail.outbox[0]

        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": forms_export.uuid},
            )
        )

        self.assertIn(download_url, sent_mail.body)
        self.assertEqual("Forms export ready", sent_mail.subject)
        self.assertIn("test@email.nl", sent_mail.to)


@temp_private_root(reset_storage=False)
class ImportFormsTaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form1, form2 = FormFactory.create_batch(2)
        user = SuperUserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
            export_options={},
        )

        cls.form_export = FormsExport.objects.get()
        cls.user = user

    def _copy_file_to_imports_tempdir(self):
        exported_zip_file = self.form_export.export_content
        exported_zip_file.seek(0)

        name = "imports/tmp_import_file.zip"
        filename = private_media_storage.save(name, exported_zip_file)

        return filename

    def test_import_forms(self):
        imported_file_path = self._copy_file_to_imports_tempdir()
        assert private_media_storage.exists(imported_file_path)
        process_forms_import(str(imported_file_path), self.user.id, import_options={})

        self.assertEqual(4, Form.objects.count())

        # Check that the import file is cleaned up
        self.assertFalse(private_media_storage.exists(imported_file_path))

    @patch(
        "openforms.forms.admin.tasks.import_form",
        side_effect=ValidationError("Something went wrong"),
    )
    def test_import_form_failure(self, m_import_form):
        imported_file_path = self._copy_file_to_imports_tempdir()
        process_forms_import(str(imported_file_path), self.user.id, import_options={})

        self.assertEqual(2, Form.objects.count())

        logs = TimelineLogProxy.objects.filter(user=self.user, object_id=self.user.id)

        self.assertEqual(1, logs.count())

        log = logs.first()
        failed_forms = log.extra_data["failed_files"]

        self.assertEqual(2, len(failed_forms))

        for item in failed_forms:
            self.assertEqual(item[1], ["Something went wrong"])

    def test_import_forms_with_form_configuration_import_option(self):
        """
        A simple test to check if the import form configuration option works correctly
        when importing a form through the task.

        More in-depth testing is done in the test_import_export.py file.
        """

        # Create an export file for a form with authentication and registration backends
        form = FormFactory.create(
            registration_backend="email",
            registration_backend_options={
                "to_emails": ["test@mail.com"],
                "payment_emails": [],
            },
            authentication_backend="digid",
        )
        # Export the form with both the registration and authentication backends
        process_forms_export(
            forms_uuids=[form.uuid],
            user_id=self.user.id,
            export_options={
                "remove_sensitive_content": False,
                "form_configuration": [
                    FormConfigurationOptions.registration_backends,
                    FormConfigurationOptions.auth_backends,
                ],
            },
        )
        self.form_export = FormsExport.objects.last()

        imported_file_path = self._copy_file_to_imports_tempdir()
        assert private_media_storage.exists(imported_file_path)
        # Import the form with only the registration backends
        process_forms_import(
            str(imported_file_path),
            self.user.id,
            import_options={
                "form_configuration": [
                    FormConfigurationOptions.registration_backends,
                ]
            },
        )

        imported_form = Form.objects.last()

        # The imported form doesn't have the authentication backend
        self.assertEqual(imported_form.auth_backends.count(), 0)

        # The imported form should have the complete registration backend configuration
        self.assertEqual(imported_form.registration_backends.count(), 1)
        registration_backend = imported_form.registration_backends.first()
        self.assertEqual(registration_backend.backend, "email")
        self.assertEqual(registration_backend.options["to_emails"], ["test@mail.com"])
        self.assertEqual(registration_backend.options["payment_emails"], [])

    def test_import_forms_with_additional_form_configuration_import_option(self):
        """
        A simple test to check if the import additional form configuration option works
        correctly when importing a form through the task.

        More in-depth testing is done in the test_import_export.py file.
        """

        # Create an export file for a form with product and Yivi attribute groups
        product = ProductFactory.create()
        yivi_attribute_group = AttributeGroupFactory.create(
            attributes=["irma-demo.gemeente.personalData.familyname"],
        )
        form = FormFactory.create(
            product=product,
            authentication_backend=YIVI_OIDC_PLUGIN_ID,
            authentication_backend__options={
                "authentication_options": [],
                "additional_attributes_groups": [yivi_attribute_group.uuid],
            },
        )
        # Export the form with both the product and Yivi attribute groups
        process_forms_export(
            forms_uuids=[form.uuid],
            user_id=self.user.id,
            export_options={
                "remove_sensitive_content": False,
                "form_configuration": [
                    FormConfigurationOptions.auth_backends,
                ],
                "additional_form_configuration": [
                    AdditionalFormConfigurationOptions.product,
                    AdditionalFormConfigurationOptions.yivi_attribute_groups,
                ],
            },
        )
        self.form_export = FormsExport.objects.last()

        imported_file_path = self._copy_file_to_imports_tempdir()
        assert private_media_storage.exists(imported_file_path)
        # Import the form with only the Yivi attribute groups
        process_forms_import(
            str(imported_file_path),
            self.user.id,
            import_options={
                "additional_form_configuration": [
                    AdditionalFormConfigurationOptions.yivi_attribute_groups,
                ]
            },
        )

        imported_form = Form.objects.last()

        # The imported form doesn't have a product
        self.assertIsNone(imported_form.product)

        # The imported form should have the yivi auth backend configuration with the
        # additional attribute groups
        self.assertEqual(imported_form.auth_backends.count(), 1)

        auth_backend = imported_form.auth_backends.first()
        self.assertEqual(auth_backend.backend, YIVI_OIDC_PLUGIN_ID)

        attribute_groups = auth_backend.options["additional_attributes_groups"]
        self.assertEqual(len(attribute_groups), 1)
        self.assertEqual(attribute_groups[0], str(yivi_attribute_group.uuid))

    def test_import_forms_with_theme_import_option(self):
        """
        A simple test to check if the import theme option works correctly when importing
        a form through the task.

        More in-depth testing is done in the test_import_export.py file.
        """
        theme = ThemeFactory.create(uuid="023d0860-0836-4d6a-b9e1-514c509c67cf")

        imported_file_path = self._copy_file_to_imports_tempdir()
        assert private_media_storage.exists(imported_file_path)
        process_forms_import(
            str(imported_file_path),
            self.user.id,
            import_options={
                "theme_uuid": str(theme.uuid),
            },
        )

        self.assertEqual(4, Form.objects.count())
        imported_forms = Form.objects.all().order_by("-id")[:2]

        # Both forms should have been imported with the same theme
        assert imported_forms[0].theme is not None
        self.assertEqual(str(imported_forms[0].theme.uuid), theme.uuid)

        assert imported_forms[1].theme is not None
        self.assertEqual(str(imported_forms[1].theme.uuid), theme.uuid)

    def test_import_forms_with_category_import_option(self):
        """
        A simple test to check if the import category option works correctly when
        importing a form through the task.

        More in-depth testing is done in the test_import_export.py file.
        """
        category = CategoryFactory.create(uuid="023d0860-0836-4d6a-b9e1-514c509c67cf")

        imported_file_path = self._copy_file_to_imports_tempdir()
        assert private_media_storage.exists(imported_file_path)
        process_forms_import(
            str(imported_file_path),
            self.user.id,
            import_options={
                "category_uuid": str(category.uuid),
            },
        )

        self.assertEqual(4, Form.objects.count())
        imported_forms = Form.objects.all().order_by("-id")[:2]

        # Both forms should have been imported with the same category
        assert imported_forms[0].category is not None
        self.assertEqual(str(imported_forms[0].category.uuid), category.uuid)

        assert imported_forms[1].category is not None
        self.assertEqual(str(imported_forms[1].category.uuid), category.uuid)
