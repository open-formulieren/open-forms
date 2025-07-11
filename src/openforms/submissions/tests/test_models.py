import os
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings, tag

from freezegun import freeze_time
from privates.test import temp_private_root

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
                "version": "v1",
                "plugin": "digid",
                "identifier": "123456782",
                "representation": "T. Hulk",
                "co_sign_auth_attribute": "bsn",
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
                "version": "v1",
                "plugin": "digid",
                "identifier": "",
                "co_sign_auth_attribute": "bsn",
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

        with (
            patch(
                "django.core.files.storage.FileSystemStorage.delete", side_effect=exc
            ) as mock_delete,
            self.captureOnCommitCallbacks(execute=True),
        ):
            submission.delete()

        mock_delete.assert_called_once_with(attachment.content.name)

        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())
        self.assertFalse(
            SubmissionFileAttachment.objects.filter(pk=attachment.pk).exists()
        )
        self.assertFalse(attachment.content.storage.exists(attachment.content.path))

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
                "version": "v1",
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
            self.assertEqual(submission1.cosign_state.email, "test@test.nl")

        with self.subTest("in fieldset"):
            self.assertEqual(submission2.cosign_state.email, "test@test.nl")

        with self.subTest("nested"):
            self.assertEqual(submission3.cosign_state.email, "test@test.nl")

    @override_settings(ALLOWED_HOSTS=["localhost"])
    def test_set_co_sign_data(self):
        form = FormFactory.create()

        with self.subTest(version="v1"):
            submission = SubmissionFactory.build(
                form=form, form_url="http://localhost/some-form"
            )
            submission.co_sign_data = {
                "version": "v1",
                "plugin": "digid",
                "identifier": "123456782",
                "representation": "John Doe",
                "co_sign_auth_attribute": AuthAttribute.bsn,
                "fields": {
                    "firstName": "John",
                    "lastName": "Doe",
                },
            }
            try:
                submission.full_clean()
            except ValidationError as exc:
                raise self.failureException("Should be valid") from exc

        with self.subTest(version="v2"):
            submission = SubmissionFactory.build(
                form=form, form_url="http://localhost/some-form"
            )
            submission.co_sign_data = {
                "version": "v2",
                "plugin": "digid",
                "attribute": "bsn",
                "value": "123456782",
                "cosign_date": "2025-01-01T00:00:00+01:00",
            }
            try:
                submission.full_clean()
            except ValidationError as exc:
                raise self.failureException("Should be valid") from exc

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


class SubmissionFileAttachmentTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = SubmissionFileAttachment()

        result = str(instance)

        self.assertIsInstance(result, str)
