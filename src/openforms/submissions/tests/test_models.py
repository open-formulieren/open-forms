import logging
import os
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings, tag

from freezegun import freeze_time
from privates.test import temp_private_root
from testfixtures import LogCapture

from openforms.authentication.service import AuthAttribute
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import Submission, SubmissionFileAttachment, SubmissionValueVariable
from .factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
    SubmissionReportFactory,
    SubmissionStepFactory,
    TemporaryFileUploadFactory,
)


@temp_private_root()
class SubmissionTests(TestCase):
    maxDiff = None

    @freeze_time("2021-11-26T17:00:00+01:00")
    @override_settings(LANGUAGE_CODE="en")
    def test_submission_str(self):
        submission = SubmissionFactory.create()
        self.assertEqual(
            str(submission), f"{submission.pk} - started on Nov. 26, 2021, 5 p.m."
        )

    def test_submission_remove_sensitive_data(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textFieldSensitive",
                        "type": "textfield",
                        "isSensitiveData": True,
                    },
                    {
                        "key": "textFieldNotSensitive",
                        "type": "textfield",
                        "isSensitiveData": False,
                    },
                    {"key": "sensitiveFile", "type": "file", "isSensitiveData": True},
                ],
            }
        )
        form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textFieldSensitive2",
                        "type": "textfield",
                        "isSensitiveData": True,
                    },
                    {
                        "key": "textFieldNotSensitive2",
                        "type": "textfield",
                        "isSensitiveData": False,
                    },
                ],
            }
        )
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)
        form_step_2 = FormStepFactory.create(
            form=form, form_definition=form_definition_2
        )

        submission = SubmissionFactory.create(form=form, auth_info__value="999990676")
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

        with self.captureOnCommitCallbacks(execute=True):
            submission.remove_sensitive_data()

        submission.refresh_from_db()
        submission_step.refresh_from_db()
        submission_step_2.refresh_from_db()

        self.assertNotIn("textFieldSensitive", submission_step.data)
        self.assertEqual(
            submission_step.data["textFieldNotSensitive"], "this is not sensitive"
        )
        self.assertNotIn("textFieldSensitive2", submission_step_2.data)
        self.assertEqual(
            submission_step_2.data["textFieldNotSensitive2"], "this is not sensitive"
        )
        self.assertTrue(submission._is_cleaned)
        self.assertEqual(submission.auth_info.value, "")

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
        with self.captureOnCommitCallbacks(execute=True):
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
                with self.captureOnCommitCallbacks(execute=True):
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
                        "type": "textfield",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "type": "textfield",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "type": "textfield",
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
                        "type": "textfield",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "type": "date",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                    {
                        "key": "phoneNumber",
                        "type": "textfield",
                        "appointments": {"phoneNumber": True},
                        "label": "Phone Number",
                    },
                    {
                        "key": "randomAttribute",
                        "type": "textfield",
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
        submission = SubmissionFactory.create(auth_info__value="bsn1")
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
        self.assertEqual(new_submission.auth_info.value, "bsn1")
        self.assertEqual(new_submission.auth_info.plugin, "digid")
        self.assertEqual(new_submission.auth_info.attribute, AuthAttribute.bsn)
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
                "co_sign_auth_attribute": "bsn",
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
        submission = SubmissionFactory.create(
            auth_info__plugin="digid",
            auth_info__value="123",
            auth_info__attribute=AuthAttribute.bsn,
        )

        self.assertEqual(submission.get_auth_mode_display(), "digid (bsn)")

    def test_is_authenticated(self):
        with self.subTest("yes"):
            submission = SubmissionFactory.create(auth_info__plugin="digid")
            self.assertTrue(submission.is_authenticated)

        with self.subTest("no"):
            submission = SubmissionFactory.create()
            self.assertFalse(submission.is_authenticated)

    def test_submission_data_with_dotted_keys(self):
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "display": "form",
                "components": [
                    {"key": "person.name", "type": "textfield", "label": "Name"},
                    {"key": "person.surname", "type": "textfield", "label": "Surname"},
                    {
                        "key": "person.pets",
                        "type": "selectboxes",
                        "label": "Pets",
                        "values": [
                            {"value": "cat", "label": "Cat"},
                            {"value": "dog", "label": "Dog"},
                            {"value": "bird", "label": "Bird"},
                        ],
                    },
                ],
            }
        )
        submission = SubmissionFactory.create(form=form_step.form)
        SubmissionStepFactory.create(
            submission=submission,
            data={
                "person": {
                    "name": "Jo",
                    "surname": "Doe",
                    "pets": {
                        "cat": True,
                        "dog": False,
                        "bird": False,
                    },
                }
            },
            form_step=form_step,
        )

        name_variable = SubmissionValueVariable.objects.get(
            submission=submission, key="person.name"
        )
        surname_variable = SubmissionValueVariable.objects.get(
            submission=submission, key="person.surname"
        )
        pet_variable = SubmissionValueVariable.objects.get(
            submission=submission, key="person.pets"
        )

        self.assertEqual(name_variable.value, "Jo")
        self.assertEqual(surname_variable.value, "Doe")
        self.assertEqual(
            pet_variable.value,
            {
                "cat": True,
                "dog": False,
                "bird": False,
            },
        )

        self.assertEqual(
            {
                "person": {
                    "name": "Jo",
                    "surname": "Doe",
                    "pets": {
                        "cat": True,
                        "dog": False,
                        "bird": False,
                    },
                }
            },
            submission.data,
        )

    def test_form_login_required(self):
        with self.subTest("form login not required"):
            submission = SubmissionFactory.create(
                form__generate_minimal_setup=True,
                form__formstep__form_definition__login_required=False,
            )

            self.assertFalse(submission.form_login_required)

        with self.subTest("form login required"):
            submission = SubmissionFactory.create(
                form__generate_minimal_setup=True,
                form__formstep__form_definition__login_required=True,
            )

            self.assertTrue(submission.form_login_required)

        with self.subTest("via annotate property, False"):
            submission = SubmissionFactory.build()
            submission._form_login_required = False

            self.assertFalse(submission.form_login_required)

        with self.subTest("via annotate property, True"):
            submission = SubmissionFactory.build()
            submission._form_login_required = True

            self.assertTrue(submission.form_login_required)

    def test_get_cosigner_email(self):
        submission1 = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Co-signer Email",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )
        submission2 = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "fieldset",
                    "type": "fieldset",
                    "components": [
                        {
                            "key": "cosign",
                            "type": "cosign",
                            "label": "Co-signer Email",
                        }
                    ],
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )
        submission3 = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "nested.cosign",
                    "type": "cosign",
                    "label": "Co-signer Email",
                },
            ],
            submitted_data={"nested": {"cosign": "test@test.nl"}},
        )

        with self.subTest("simple"):
            self.assertEqual(submission1.cosigner_email, "test@test.nl")

        with self.subTest("in fieldset"):
            self.assertEqual(submission2.cosigner_email, "test@test.nl")

        with self.subTest("nested"):
            self.assertEqual(submission3.cosigner_email, "test@test.nl")

    def test_clear_execution_state_without_execution_state(self):
        submission = SubmissionFactory.create()

        self.assertFalse(hasattr(submission, "_execution_state"))

        submission.clear_execution_state()

    @tag("gh-3470")
    def test_names_do_not_break_pdf_saving_to_disk(self):
        report = SubmissionReportFactory.create(submission__form__name="not/a/path")
        report.generate_submission_report_pdf()

        self.assertTrue(report.content.storage.exists(report.content.name))

    @tag("gh-5035")
    def test_total_configuration_wrapper_does_not_mutate_first_step(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textfield1",
                        "type": "textfield",
                        "label": "textfield",
                    }
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            order=1,
            form_definition__configuration={
                "components": [
                    {
                        "key": "textfield2",
                        "type": "textfield",
                        "label": "Text field 2",
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)

        configuration_wrapper = submission.total_configuration_wrapper

        with self.subTest("all keys present"):
            self.assertIn("textfield1", configuration_wrapper)
            self.assertIn("textfield2", configuration_wrapper)

        step1, step2 = submission.steps

        with self.subTest("step 1 keys"):
            step1_keys = [
                c["key"]
                for c in step1.form_step.form_definition.configuration["components"]
            ]
            self.assertEqual(step1_keys, ["textfield1"])

        with self.subTest("step 2 keys"):
            step2_keys = [
                c["key"]
                for c in step2.form_step.form_definition.configuration["components"]
            ]
            self.assertEqual(step2_keys, ["textfield2"])


class TemporaryFileUploadTests(TestCase):
    def test_legacy_check_constraint(self):
        with self.assertRaises(IntegrityError):
            TemporaryFileUploadFactory.create(
                submission=None,
                legacy=False,
            )

    def test_non_legacy_check_constraint(self):
        with self.assertRaises(IntegrityError):
            TemporaryFileUploadFactory.create(
                submission=SubmissionFactory.create(),
                legacy=True,
            )
