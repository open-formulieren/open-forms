import logging
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase, override_settings

from freezegun import freeze_time

from openforms.logging.models import TimelineLogProxy

from ..tasks import activate_forms, deactivate_forms
from .factories import FormFactory

logger = logging.getLogger(__name__)


class ActivateFormsTests(TestCase):
    @freeze_time("2023-10-10T21:15:00Z")
    def test_forms_are_activated_on_specified_datetime(self):
        form1 = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")
        form2 = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")

        with self.captureOnCommitCallbacks(execute=True):
            activate_forms()

        form1.refresh_from_db()
        form2.refresh_from_db()

        self.assertTrue(form1.active)
        self.assertIsNone(form1.activate_on)
        self.assertTrue(form2.active)
        self.assertIsNone(form2.activate_on)

        # make sure the activation is logged as well
        log_entries = TimelineLogProxy.objects.all()
        self.assertEqual(log_entries.count(), 2)

        with override_settings(LANGUAGE_CODE="en"):
            for log_entry in log_entries:
                message = log_entry.get_message()

                self.assertEqual(
                    message.strip().replace("&quot;", '"'),
                    f"{log_entry.fmt_lead}: Form was activated.",
                )

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_with_timedelta(self):
        with self.subTest("5 min have not passed"):
            form = FormFactory(active=False, activate_on="2023-10-10T21:12:00Z")

            activate_forms()

            form.refresh_from_db()

            self.assertTrue(form.active)
            self.assertIsNone(form.activate_on)

        with self.subTest("5 min have passed"):
            form = FormFactory(active=False, activate_on="2023-10-10T21:08:00Z")

            activate_forms()

            form.refresh_from_db()

            self.assertFalse(form.active)
            self.assertIsNotNone(form.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_activated_on_different_date(self):
        form = FormFactory(active=False, activate_on="2023-10-19T21:15:00Z")

        activate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_activated_on_different_time(self):
        form = FormFactory(active=False, activate_on="2023-10-10T21:16:00Z")

        activate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_activated_when_soft_deleted(self):
        form = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")
        form._is_deleted = True
        form.save(update_fields=["_is_deleted"])

        activate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.activate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    @patch("openforms.forms.tasks.Form.activate")
    def test_database_error(self, mocked_activation):
        form = FormFactory(active=False, activate_on="2023-10-10T21:15:00Z")
        mocked_activation.side_effect = DatabaseError()

        with self.assertLogs() as logs:
            activate_forms()

        message = logs.records[0].getMessage()

        mocked_activation.assert_called()
        self.assertEqual(message, f"Form activation of form {form.admin_name} failed")


class DeactivateFormsTests(TestCase):
    @freeze_time("2023-10-10T21:15:00Z")
    def test_forms_are_deactivated_on_specified_datetime(self):
        form1 = FormFactory(deactivate_on="2023-10-10T21:15:00Z")
        form2 = FormFactory(deactivate_on="2023-10-10T21:15:00Z")

        with self.captureOnCommitCallbacks(execute=True):
            deactivate_forms()

        form1.refresh_from_db()
        form2.refresh_from_db()

        self.assertFalse(form1.active)
        self.assertIsNone(form1.deactivate_on)
        self.assertFalse(form2.active)
        self.assertIsNone(form2.deactivate_on)

        # make sure the deactivation is logged as well
        log_entries = TimelineLogProxy.objects.all()
        self.assertEqual(log_entries.count(), 2)

        with override_settings(LANGUAGE_CODE="en"):
            for log_entry in log_entries:
                message = log_entry.get_message()

                self.assertEqual(
                    message.strip().replace("&quot;", '"'),
                    f"{log_entry.fmt_lead}: Form was deactivated.",
                )

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_with_timedelta(self):
        with self.subTest("5 min have not passed"):
            form = FormFactory(deactivate_on="2023-10-10T21:12:00Z")

            deactivate_forms()

            form.refresh_from_db()

            self.assertFalse(form.active)
            self.assertIsNone(form.deactivate_on)

        with self.subTest("5 min have passed"):
            form = FormFactory(deactivate_on="2023-10-10T21:08:00Z")

            deactivate_forms()

            form.refresh_from_db()

            self.assertTrue(form.active)
            self.assertIsNotNone(form.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_deactivated_on_different_date(self):
        form = FormFactory(deactivate_on="2023-10-19T21:15:00Z")

        deactivate_forms()

        form.refresh_from_db()

        self.assertTrue(form.active)
        self.assertIsNotNone(form.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_deactivated_on_different_time(self):
        form = FormFactory(deactivate_on="2023-10-10T21:16:00Z")

        deactivate_forms()

        form.refresh_from_db()

        self.assertTrue(form.active)
        self.assertIsNotNone(form.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    def test_form_is_not_deactivated_when_soft_deleted(self):
        form = FormFactory(active=False, deactivate_on="2023-10-10T21:15:00Z")
        form._is_deleted = True
        form.save(update_fields=["_is_deleted"])

        deactivate_forms()

        form.refresh_from_db()

        self.assertFalse(form.active)
        self.assertIsNotNone(form.deactivate_on)

    @freeze_time("2023-10-10T21:15:00Z")
    @patch("openforms.forms.tasks.Form.deactivate")
    def test_database_error(self, mocked_deactivation):
        form = FormFactory(deactivate_on="2023-10-10T21:15:00Z")
        mocked_deactivation.side_effect = DatabaseError()

        with self.assertLogs() as logs:
            deactivate_forms()

        message = logs.records[0].getMessage()

        mocked_deactivation.assert_called()
        self.assertEqual(message, f"Form deactivation of form {form.admin_name} failed")
