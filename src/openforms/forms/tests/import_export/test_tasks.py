import zipfile
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID

from django.core import mail
from django.core.files.storage import storages
from django.test import TestCase, override_settings
from django.urls import reverse

import time_machine
from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from privates.test import temp_private_root
from rest_framework.exceptions import ValidationError

from openforms.accounts.tests.factories import UserFactory
from openforms.config.tests.factories import ThemeFactory
from openforms.logging.models import TimelineLogProxy
from openforms.utils.urls import build_absolute_uri

from ...admin.tasks import process_forms_export, process_forms_import
from ...import_export.service import (
    AdditionalFormConfigurationOptions,
    FormConfigurationOptions,
    FormExportOptions,
    FormImportOptions,
    export_multiple_forms,
)
from ...models import Form, FormsExport
from ..factories import CategoryFactory, FormFactory


@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class ExportFormsTaskTests(TestCase):
    @time_machine.travel("2022-02-21T00:00:00+00:00", tick=False)
    def test_bulk_export_produces_zip_file_with_nested_exports(self):
        form1, form2 = FormFactory.create_batch(2)
        user = UserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
            export_options={},
        )

        # we expect exactly one export record to be created
        forms_export = FormsExport.objects.get()
        self.assertEqual(
            forms_export.datetime_requested, datetime(2022, 2, 21, 0, 0, 0, tzinfo=UTC)
        )
        self.assertEqual(forms_export.user, user)

        with (
            self.subTest("verify export content"),
            forms_export.export_content.open("rb") as content,
            zipfile.ZipFile(content, "r") as zf,
        ):
            expected_names = {
                f"form_{form1.slug}.zip",
                f"form_{form2.slug}.zip",
            }
            self.assertEqual(set(zf.namelist()), expected_names)

        with self.subTest("notification email"):
            self.assertEqual(len(mail.outbox), 1)
            sent_mail = mail.outbox[0]

            download_url = build_absolute_uri(
                reverse(
                    "admin:download_forms_export",
                    kwargs={"uuid": forms_export.uuid},
                )
            )

            self.assertIn(download_url, str(sent_mail.body))
            self.assertEqual("Forms export ready", sent_mail.subject)
            self.assertIn("test@email.nl", sent_mail.to)


@temp_private_root()  # uses an in-memory storage
class ImportFormsTaskTests(HypothesisTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create()

    def test_task_imports_forms_from_file_storage(self):
        forms = FormFactory.create_batch(2)
        storage = storages["privates"]
        with storage.open("export.zip", "wb") as outfile:
            export_multiple_forms(
                [form.uuid for form in forms],
                export_options=FormExportOptions(),
                target=outfile,
            )

        process_forms_import("export.zip", user_id=self.user.pk, import_options={})

        # 2 pre-existing and those have been imported again
        self.assertEqual(Form.objects.count(), 4)
        self.assertFalse(storage.exists("export.zip"))

    def test_import_failures_are_handled_and_not_fatal(self):
        form = FormFactory.create()
        storage = storages["privates"]
        with storage.open("export.zip", "wb") as outfile:
            export_multiple_forms(
                [form.uuid], export_options=FormExportOptions(), target=outfile
            )

        with patch(
            "openforms.forms.import_export.import_form.import_form_data",
            side_effect=ValidationError("Something went wrong"),
        ) as mock_import_form_data:
            process_forms_import("export.zip", user_id=self.user.pk, import_options={})

        mock_import_form_data.assert_called_once()
        with self.subTest("no new form created due to failures"):
            self.assertEqual(Form.objects.count(), 1)

        with self.subTest("failures are logged"):
            log = TimelineLogProxy.objects.filter_event("bulk_forms_imported").get()
            self.assertEqual(log.user, self.user)
            failed_forms = log.extra_data["failed_files"]
            self.assertEqual(
                failed_forms,
                [
                    [f"form_{form.slug}.zip", ["Something went wrong"]],
                ],
            )

    @settings(suppress_health_check=[HealthCheck.too_slow])
    @given(
        configuration=st.lists(
            elements=st.sampled_from(FormConfigurationOptions),
            unique=True,
        ),
        additional_configuration=st.lists(
            elements=st.sampled_from(AdditionalFormConfigurationOptions),
            unique=True,
        ),
        theme_uuid=st.one_of(st.uuids(version=4), st.none()),
        category_uuid=st.one_of(st.uuids(version=4), st.none()),
    )
    def test_task_import_options_forwarded_to_import_function(
        self,
        configuration: list[FormConfigurationOptions],
        additional_configuration: list[AdditionalFormConfigurationOptions],
        theme_uuid: UUID | None,
        category_uuid: UUID | None,
    ):
        """
        Assert that import options are forwarded to the actual importer.

        The details of the import options are covered in the ``test_import.py`` module.
        """
        form = FormFactory.create()
        storage = storages["privates"]
        with storage.open("export.zip", "wb") as outfile:
            export_multiple_forms(
                [form.uuid], export_options=FormExportOptions(), target=outfile
            )

        expected = FormImportOptions(
            form_configuration=configuration,
            additional_form_configuration=additional_configuration,
            theme=ThemeFactory.create(uuid=theme_uuid) if theme_uuid else None,
            category=CategoryFactory.create(uuid=category_uuid)
            if category_uuid
            else None,
        )

        import_options_dict = {
            "form_configuration": configuration,
            "additional_form_configuration": additional_configuration,
        }
        if theme_uuid:
            import_options_dict["theme_uuid"] = theme_uuid
        if category_uuid:
            import_options_dict["category_uuid"] = category_uuid
        with patch(
            "openforms.forms.import_export.import_form.import_form_data",
        ) as mock_import_form_data:
            process_forms_import(
                "export.zip", user_id=self.user.pk, import_options=import_options_dict
            )

        mock_import_form_data.assert_called_once()
        self.assertEqual(mock_import_form_data.call_args[0][1], expected)
