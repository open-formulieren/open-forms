import logging
import os
from collections import OrderedDict
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from privates.test import temp_private_root
from testfixtures import LogCapture

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import Submission, SubmissionFileAttachment
from .factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionStepFactory,
)


@temp_private_root()
class SubmissionTests(TestCase):
    maxDiff = None

    def test_get_merged_data(self):
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"key1": "value1", "key2": "value2"},
            form_step=FormStepFactory.create(),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"key2": "value-a", "key3": "value-b"},
            form_step=FormStepFactory.create(),
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=FormStepFactory.create()
        )

        self.assertEqual(
            submission.get_merged_data(),
            {"key1": "value1", "key2": "value-a", "key3": "value-b"},
        )

    def test_get_ordered_data_with_component_type_formio_formatters(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "key", "type": "textfield", "label": "Label"},
                    {"key": "key2", "type": "textarea", "label": "Label2"},
                    {"key": "key3", "type": "checkbox", "label": "Label3"},
                    {
                        "key": "key4",
                        "type": "fieldset",
                        "components": [{"key": "key5", "type": "textfield"}],
                    },
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"key3": True, "key2": "this is text in a text area"},
            form_step__form_definition=form_definition,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "key5": "this is some inner text",
                "key": "this is some text",
                "key2": "this is other text in a text area",
            },
            form_step__form_definition=form_definition,
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form_definition=form_definition,
        )
        actual = submission.get_ordered_data_with_component_type()
        expected = OrderedDict(
            [
                (
                    "key",
                    (
                        {
                            "key": "key",
                            "type": "textfield",
                            "label": "Label",
                        },
                        "this is some text",
                    ),
                ),
                (
                    "key2",
                    (
                        {
                            "key": "key2",
                            "type": "textarea",
                            "label": "Label2",
                        },
                        "this is other text in a text area",
                    ),
                ),
                (
                    "key3",
                    (
                        {
                            "key": "key3",
                            "type": "checkbox",
                            "label": "Label3",
                        },
                        True,
                    ),
                ),
                (
                    "key5",
                    (
                        {
                            "key": "key5",
                            "type": "textfield",
                            "label": "key5",
                        },
                        "this is some inner text",
                    ),
                ),
            ]
        )
        self.assertEqual(actual, expected)

    def test_get_printable_data_with_selectboxes_formio_formatters(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "testSelectBoxes",
                        "type": "selectboxes",
                        "label": "My Boxes",
                        "values": [
                            {"value": "test1", "label": "test 1", "shortcut": ""},
                            {"value": "test2", "label": "test 2", "shortcut": ""},
                            {"value": "test3", "label": "test 3", "shortcut": ""},
                        ],
                    },
                ],
            }
        )
        submission = SubmissionFactory.create()
        SubmissionStepFactory.create(
            submission=submission,
            data={"testSelectBoxes": {"test1": True, "test2": True, "test3": False}},
            form_step=FormStepFactory.create(
                form=submission.form, form_definition=form_definition
            ),
        )

        ordered = submission.get_ordered_data_with_component_type()
        self.assertEqual(
            ordered,
            {
                "testSelectBoxes": (
                    {
                        "key": "testSelectBoxes",
                        "type": "selectboxes",
                        "label": "My Boxes",
                        "values": [
                            {"value": "test1", "label": "test 1", "shortcut": ""},
                            {"value": "test2", "label": "test 2", "shortcut": ""},
                            {"value": "test3", "label": "test 3", "shortcut": ""},
                        ],
                    },
                    {"test1": True, "test2": True, "test3": False},
                )
            },
        )
        printable_data = submission.get_printable_data()

        self.assertEqual(
            "My Boxes",
            printable_data[0][0],
        )
        self.assertEqual(
            "test 1; test 2",
            printable_data[0][1],
        )

    def test_submission_remove_sensitive_data(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive", "isSensitiveData": False},
                    {"key": "sensitiveFile", "type": "file", "isSensitiveData": True},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive2", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive2", "isSensitiveData": False},
                ],
            }
        )
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )

        submission = SubmissionFactory.create(
            form=form, bsn="999990676", kvk="69599084", prefill_data={"secret": "123"}
        )
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={
                "textFieldSensitive": "this is sensitive",
                "textFieldNotSensitive": "this is not sensitive",
            },
            form_step=form_step,
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step=submission_step, form_key="sensitiveFile"
        )
        submission_step_2 = SubmissionStepFactory.create(
            submission=submission,
            data={
                "textFieldSensitive2": "this is sensitive",
                "textFieldNotSensitive2": "this is not sensitive",
            },
            form_step=form_step_2,
        )
        with self.subTest("validate testdata setup"):
            self.assertTrue(attachment.content.storage.exists(attachment.content.name))

        with capture_on_commit_callbacks(execute=True):
            submission.remove_sensitive_data()

        submission.refresh_from_db()
        submission_step.refresh_from_db()
        submission_step_2.refresh_from_db()

        self.assertEqual(submission_step.data["textFieldSensitive"], "")
        self.assertEqual(
            submission_step.data["textFieldNotSensitive"], "this is not sensitive"
        )
        self.assertEqual(submission_step_2.data["textFieldSensitive2"], "")
        self.assertEqual(
            submission_step_2.data["textFieldNotSensitive2"], "this is not sensitive"
        )
        self.assertTrue(submission._is_cleaned)
        self.assertEqual(submission.bsn, "")
        self.assertEqual(submission.kvk, "")
        self.assertEqual(submission.prefill_data, {})

        with self.subTest("attachment deletion"):
            self.assertFalse(attachment.content.storage.exists(attachment.content.name))
            self.assertFalse(
                SubmissionFileAttachment.objects.filter(pk=attachment.pk).exists()
            )

    def test_submission_remove_sensitive_co_sign_data(self):
        """
        Assert that the sensitive (source) data for co-signed submissions is wiped.

        We do keep the representation, as that is used in PDF and confirmation e-mail
        generation and is usually a label derived from the source fields.
        """
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": "digid",
                "identifier": "123456782",
                "representation": "T. Hulk",
                "fields": {
                    "firstName": "The",
                    "lastName": "Hulk",
                },
            }
        )

        submission.remove_sensitive_data()

        submission.refresh_from_db()
        self.assertEqual(
            submission.co_sign_data,
            {
                "plugin": "digid",
                "identifier": "",
                "fields": {},
                "representation": "T. Hulk",
            },
        )

    def test_submission_delete_file_uploads_cascade(self):
        """
        Assert that when a submission is deleted, the file uploads (on disk!) are deleted.
        """
        submission = SubmissionFactory.create(
            completed=True, form__generate_minimal_setup=True
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission=submission
        )
        with self.subTest("test setup validation"):
            self.assertTrue(attachment.content.storage.exists(attachment.content.path))

        # delete the submission, it must cascade
        with capture_on_commit_callbacks(execute=True):
            submission.delete()

        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())
        self.assertFalse(
            SubmissionFileAttachment.objects.filter(pk=attachment.pk).exists()
        )
        self.assertFalse(attachment.content.storage.exists(attachment.content.path))

    def test_submission_delete_file_uploads_cascade_file_already_gone(self):
        """
        Assert that when a submission is deleted, the file uploads (on disk!) are deleted.
        """
        submission = SubmissionFactory.create(
            completed=True, form__generate_minimal_setup=True
        )
        attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission=submission
        )
        os.remove(attachment.content.path)
        with self.subTest("test setup validation"):
            self.assertFalse(attachment.content.storage.exists(attachment.content.path))

        # delete the submission, it must cascade
        exc = Exception("Delete failed")

        with patch(
            "django.core.files.storage.FileSystemStorage.delete", side_effect=exc
        ) as mock_delete:
            with LogCapture(level=logging.WARNING) as capture:
                with capture_on_commit_callbacks(execute=True):
                    submission.delete()

        mock_delete.assert_called_once_with(attachment.content.name)
        capture.check(
            (
                "openforms.utils.files",
                "WARNING",
                "File delete on model %r (pk=%s, field=content, path=%s) failed: Delete failed"
                % (
                    SubmissionFileAttachment,
                    attachment.pk,
                    attachment.content.path,
                ),
            ),
        )

        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())
        self.assertFalse(
            SubmissionFileAttachment.objects.filter(pk=attachment.pk).exists()
        )
        self.assertFalse(attachment.content.storage.exists(attachment.content.path))

    def test_get_merged_appointment_data(self):
        form = FormFactory.create()
        form_definition_1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "lastName",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                    {
                        "key": "phoneNumber",
                        "appointments": {"phoneNumber": True},
                        "label": "Phone Number",
                    },
                    {
                        "key": "randomAttribute",
                        "appointments": {"birthDate": False},
                        "label": "Random attribute",
                    },
                ],
            }
        )
        form_step_1 = FormStepFactory.create(
            form=form, form_definition=form_definition_1
        )
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "location": {"identifier": "1", "name": "Amsterdam"},
                "time": "2021-08-25T17:00:00",
            },
            form_step=form_step_1,
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "lastName": "Maykin",
                "birthDate": "1990-08-01",
                "phoneNumber": "+31 20 753 05 23",
                "randomAttribute": "This is some random stuff",
            },
            form_step=form_step_2,
        )

        self.assertEqual(
            submission.get_merged_appointment_data(),
            {
                "productIDAndName": {
                    "label": "Product",
                    "value": {"identifier": "79", "name": "Paspoort"},
                },
                "locationIDAndName": {
                    "label": "Location",
                    "value": {"identifier": "1", "name": "Amsterdam"},
                },
                "appStartTime": {"label": "Time", "value": "2021-08-25T17:00:00"},
                "clientLastName": {"label": "Last Name", "value": "Maykin"},
                "clientDateOfBirth": {"label": "Date of Birth", "value": "1990-08-01"},
                "clientPhoneNumber": {
                    "label": "Phone Number",
                    "value": "+31 20 753 05 23",
                },
            },
        )

    def test_copy_submission(self):
        submission = SubmissionFactory.create(
            kvk="kvk1", bsn="bsn1", pseudo="pseudo1", auth_plugin="digid"
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"key1": "value1", "key2": "value2"},
            form_step=FormStepFactory.create(),
        )
        SubmissionStepFactory.create(
            submission=submission,
            data={"key3": "value-b"},
            form_step=FormStepFactory.create(),
        )

        new_submission = Submission.objects.copy(submission)

        self.assertEqual(new_submission.form, submission.form)
        self.assertEqual(new_submission.form_url, submission.form_url)
        self.assertEqual(new_submission.previous_submission, submission)
        self.assertEqual(new_submission.data, submission.data)
        self.assertEqual(new_submission.kvk, "kvk1")
        self.assertEqual(new_submission.bsn, "bsn1")
        self.assertEqual(new_submission.pseudo, "pseudo1")
        self.assertEqual(new_submission.auth_plugin, "digid")
        self.assertNotEqual(new_submission.id, submission.id)
        self.assertNotEqual(new_submission.uuid, submission.uuid)

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_co_sign_data_validation(self):
        extra_fields = {
            "form": FormFactory.create(),
            "form_url": "https://example.com/test",
        }
        invalid_values = [
            {"invalid": "shape"},
            {
                "plugin": "invalid-plugin",
                "identifier": "123456782",
                "fields": {
                    "name": "Jane Doe",
                },
            },
            {"plugin": "digid"},
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                submission = SubmissionFactory.build(co_sign_data=value, **extra_fields)

                with self.assertRaises(ValidationError):
                    submission.full_clean()

    @override_settings(CORS_ALLOW_ALL_ORIGINS=True)
    def test_co_sign_data_valid_values(self):
        extra_fields = {
            "form": FormFactory.create(),
            "form_url": "https://example.com/test",
        }
        values = [
            {},
            None,
            {
                "plugin": "digid",
                "identifier": "123456782",
                "fields": {
                    "name": "Jane Doe",
                },
            },
        ]

        for value in values:
            with self.subTest(value=value):
                submission = SubmissionFactory.build(co_sign_data=value, **extra_fields)

                try:
                    submission.full_clean()
                except ValidationError as exc:
                    self.fail(f"Unexpected validation error(s): {exc}")

    def test_get_auth_mode_display(self):
        submission = SubmissionFactory.build(auth_plugin="digid", bsn="123", kvk="123")

        self.assertEqual(submission.get_auth_mode_display(), "digid (bsn,kvk)")

    def test_is_authenticated(self):
        with self.subTest("yes"):
            submission = SubmissionFactory.build(auth_plugin="digid")
            self.assertTrue(submission.is_authenticated)

        with self.subTest("no"):
            submission = SubmissionFactory.build(auth_plugin="")
            self.assertFalse(submission.is_authenticated)

    @override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
    )
    def test_hash_identifying_attributes_after_completion(self):
        """
        Test that the factory properly hashes the identifying attributes.
        """
        attrs = {
            "bsn": "000000000",
            "kvk": "123455789",
            "pseudo": "some-pseudo",
        }
        submission = SubmissionFactory.create(
            **attrs,
            completed=True,
            with_hashed_identifying_attributes=True,
        )

        submission.refresh_from_db()

        for attr, original_value in attrs.items():
            with self.subTest(**{attr: original_value}):
                current_val = getattr(submission, attr)
                self.assertNotEqual(current_val, original_value)
                self.assertTrue(current_val.startswith("pbkdf2_sha256$"))
