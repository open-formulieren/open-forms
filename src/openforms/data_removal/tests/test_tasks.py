from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils import timezone

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)

from ...forms.models import FormStep, FormVariable
from ..constants import RemovalMethods
from ..tasks import delete_submissions, make_sensitive_data_anonymous


class DeleteSubmissionsTask(TestCase):
    def test_successful_submissions_correctly_deleted(self):
        config = GlobalConfiguration.get_solo()

        # Not successful
        SubmissionFactory.create(registration_status=RegistrationStatuses.failed)
        # Too recent
        SubmissionFactory.create(registration_status=RegistrationStatuses.success)

        anonymous_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success,
            form__successful_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success
        )

        # Passing created_on to the factory create method does not work
        anonymous_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        anonymous_submission.save()
        submission_to_be_deleted.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 3)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()

    def test_successful_submissions_with_form_settings_override_global_configuration(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        form_longer_limit = FormFactory.create(
            successful_submissions_removal_limit=config.successful_submissions_removal_limit
            + 7
        )
        form_make_anonymous = FormFactory.create(
            successful_submissions_removal_method=RemovalMethods.make_anonymous
        )

        submission_longer_limit = SubmissionFactory.create(
            form=form_longer_limit,
            registration_status=RegistrationStatuses.success,
        )
        submission_anonymous = SubmissionFactory.create(
            form=form_make_anonymous,
            registration_status=RegistrationStatuses.success,
        )

        submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success
        )
        # Passing created_on to the factory create method does not work
        submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_longer_limit.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_anonymous.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_to_be_deleted.save()
        submission_longer_limit.save()
        submission_anonymous.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 2)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()

    def test_incomplete_submissions_correctly_deleted(self):
        config = GlobalConfiguration.get_solo()

        # Not in progress
        SubmissionFactory.create(registration_status=RegistrationStatuses.failed)
        # Too recent
        SubmissionFactory.create(registration_status=RegistrationStatuses.pending)
        SubmissionFactory.create(registration_status=RegistrationStatuses.in_progress)

        anonymous_pending_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending,
            form__incomplete_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        pending_submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending
        )
        anonymous_in_progress_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress,
            form__incomplete_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        in_progress_submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress
        )

        # Passing created_on to the factory create method does not work
        anonymous_pending_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        pending_submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        anonymous_in_progress_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        in_progress_submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        anonymous_pending_submission.save()
        pending_submission_to_be_deleted.save()
        anonymous_in_progress_submission.save()
        in_progress_submission_to_be_deleted.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 5)
        with self.assertRaises(ObjectDoesNotExist):
            pending_submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            pending_submission_to_be_deleted.refresh_from_db()

    def test_incomplete_submissions_with_form_settings_override_global_configuration(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        form_longer_limit = FormFactory.create(
            incomplete_submissions_removal_limit=config.incomplete_submissions_removal_limit
            + 7
        )
        form_make_anonymous = FormFactory.create(
            incomplete_submissions_removal_method=RemovalMethods.make_anonymous
        )

        pending_submission_longer_limit = SubmissionFactory.create(
            form=form_longer_limit,
            registration_status=RegistrationStatuses.pending,
        )
        pending_submission_anonymous = SubmissionFactory.create(
            form=form_make_anonymous,
            registration_status=RegistrationStatuses.pending,
        )
        in_progress_submission_longer_limit = SubmissionFactory.create(
            form=form_longer_limit,
            registration_status=RegistrationStatuses.in_progress,
        )
        in_progress_submission_anonymous = SubmissionFactory.create(
            form=form_make_anonymous,
            registration_status=RegistrationStatuses.in_progress,
        )

        pending_submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress
        )
        in_progress_submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress
        )
        # Passing created_on to the factory create method does not work
        pending_submission_longer_limit.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_submission_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_submission_longer_limit.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_submission_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_submission_longer_limit.save()
        pending_submission_anonymous.save()
        in_progress_submission_longer_limit.save()
        in_progress_submission_anonymous.save()
        pending_submission_to_be_deleted.save()
        in_progress_submission_to_be_deleted.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 4)
        with self.assertRaises(ObjectDoesNotExist):
            pending_submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            in_progress_submission_to_be_deleted.refresh_from_db()

    def test_failed_submissions_correctly_deleted(self):
        config = GlobalConfiguration.get_solo()

        # Not failed
        SubmissionFactory.create(registration_status=RegistrationStatuses.success)
        # Too recent
        SubmissionFactory.create(registration_status=RegistrationStatuses.failed)

        anonymous_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed,
            form__errored_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed
        )

        # Passing created_on to the factory create method does not work
        anonymous_submission.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        anonymous_submission.save()
        submission_to_be_deleted.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 3)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()

    def test_failed_submissions_with_form_settings_override_global_configuration(self):
        config = GlobalConfiguration.get_solo()
        form_longer_limit = FormFactory.create(
            errored_submissions_removal_limit=config.errored_submissions_removal_limit
            + 7
        )
        form_make_anonymous = FormFactory.create(
            errored_submissions_removal_method=RemovalMethods.make_anonymous
        )

        submission_longer_limit = SubmissionFactory.create(
            form=form_longer_limit,
            registration_status=RegistrationStatuses.failed,
        )
        submission_anonymous = SubmissionFactory.create(
            form=form_make_anonymous,
            registration_status=RegistrationStatuses.failed,
        )

        submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed
        )
        # Passing created_on to the factory create method does not work
        submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_longer_limit.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_anonymous.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_to_be_deleted.save()
        submission_longer_limit.save()
        submission_anonymous.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 2)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()

    def test_all_submissions_correctly_deleted(self):
        config = GlobalConfiguration.get_solo()

        # Recent submission
        SubmissionFactory.create(
            form__errored_submissions_removal_method=RemovalMethods.make_anonymous,
        )

        old_submission = SubmissionFactory.create()
        old_submission.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        old_submission.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 1)
        with self.assertRaises(ObjectDoesNotExist):
            old_submission.refresh_from_db()

    def test_all_submissions_with_form_settings_override_global_configuration(self):
        config = GlobalConfiguration.get_solo()
        form_longer_limit = FormFactory.create(
            errored_submissions_removal_limit=config.errored_submissions_removal_limit
            + 7
        )

        # Recent submission
        SubmissionFactory.create(
            form__errored_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        submission_longer_limit = SubmissionFactory.create(
            form=form_longer_limit,
            registration_status=RegistrationStatuses.failed,
        )
        submission_to_be_deleted = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed
        )
        # Passing created_on to the factory create method does not work
        submission_to_be_deleted.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_longer_limit.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )

        submission_to_be_deleted.save()
        submission_longer_limit.save()

        delete_submissions()

        self.assertEqual(Submission.objects.count(), 2)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()


class MakeSensitiveDataAnonymousTask(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive", "isSensitiveData": False},
                ],
            }
        )
        cls.form_definition_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "textFieldSensitive2", "isSensitiveData": True},
                    {"key": "textFieldNotSensitive2", "isSensitiveData": False},
                ],
            }
        )
        cls.form = FormFactory.create(
            successful_submissions_removal_method=RemovalMethods.make_anonymous,
            incomplete_submissions_removal_method=RemovalMethods.make_anonymous,
            errored_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        cls.step1 = FormStepFactory.create(
            form=cls.form, form_definition=cls.form_definition
        )
        cls.step2 = FormStepFactory.create(
            form=cls.form, form_definition=cls.form_definition_2
        )
        cls._create_form_variables(cls.form)

    @staticmethod
    def _create_form_variables(form):
        form_steps = list(FormStep.objects.filter(form=form).order_by("pk"))
        if not len(form_steps):
            form_step1 = FormStepFactory.create(form=form)
            form_step2 = FormStepFactory.create(form=form)
            form_steps = [form_step1, form_step2]

        FormVariableFactory.create(
            key="textFieldSensitive",
            is_sensitive_data=True,
            form_definition=form_steps[0].form_definition,
            form=form,
        )
        FormVariableFactory.create(
            key="textFieldNotSensitive",
            is_sensitive_data=False,
            form_definition=form_steps[0].form_definition,
            form=form,
        )
        FormVariableFactory.create(
            key="textFieldSensitive2",
            is_sensitive_data=True,
            form_definition=form_steps[1].form_definition,
            form=form,
        )
        FormVariableFactory.create(
            key="textFieldNotSensitive2",
            is_sensitive_data=False,
            form_definition=form_steps[1].form_definition,
            form=form,
        )

    def _create_submission_variables(self, submission):
        form_variables = FormVariable.objects.filter(form=submission.form)

        SubmissionValueVariableFactory.create(
            submission=submission,
            form_variable=form_variables.get(key="textFieldSensitive"),
            key="textFieldSensitive",
            value="This is sensitive",
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            form_variable=form_variables.get(key="textFieldNotSensitive"),
            key="textFieldNotSensitive",
            value="This is not sensitive",
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            form_variable=form_variables.get(key="textFieldSensitive2"),
            key="textFieldSensitive2",
            value="This is also sensitive",
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            form_variable=form_variables.get(key="textFieldNotSensitive2"),
            key="textFieldNotSensitive2",
            value="This is also not sensitive",
        )

    def test_certain_successful_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        # Not successful
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success, form=self.form
        )

        delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success,
            form__successful_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.success
        )

        # Passing created_on to the factory create method does not work
        delete_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        delete_submission.save()
        submission_to_be_anonymous.save()

        self._create_form_variables(delete_submission.form)

        for submission in [
            not_successful,
            too_recent,
            delete_submission,
            submission_to_be_anonymous,
        ]:
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )
            self._create_submission_variables(submission)

        make_sensitive_data_anonymous()

        not_successful.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [not_successful, too_recent, delete_submission]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldSensitive"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldNotSensitive"
                ],
                "This is not sensitive",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldSensitive2"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldNotSensitive2"
                ],
                "This is also not sensitive",
            )
            self.assertTrue(submission_to_be_anonymous._is_cleaned)

    def test_form_override_of_successful_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        override_form = FormFactory.create(
            successful_submissions_removal_method=RemovalMethods.make_anonymous,
            successful_submissions_removal_limit=config.successful_submissions_removal_limit
            + 7,
        )

        override_submission = SubmissionFactory.create(
            form=override_form, registration_status=RegistrationStatuses.success
        )

        # Not successful
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success, form=self.form
        )

        delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success,
            form__successful_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.success
        )

        # Passing created_on to the factory create method does not work
        delete_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        override_submission.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        delete_submission.save()
        submission_to_be_anonymous.save()

        self._create_form_variables(override_form)
        self._create_form_variables(delete_submission.form)

        for submission in [
            not_successful,
            too_recent,
            delete_submission,
            submission_to_be_anonymous,
            override_submission,
        ]:
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )
            self._create_submission_variables(submission)

        make_sensitive_data_anonymous()

        not_successful.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [
            not_successful,
            too_recent,
            delete_submission,
            override_submission,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldSensitive"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldNotSensitive"
                ],
                "This is not sensitive",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldSensitive2"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldNotSensitive2"
                ],
                "This is also not sensitive",
            )
            self.assertTrue(submission_to_be_anonymous._is_cleaned)

    def test_certain_incomplete_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        # Not pending or in_progress
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        pending_too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending, form=self.form
        )
        in_progress_too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress, form=self.form
        )

        pending_delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending,
            form__incomplete_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        in_progress_delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress,
            form__incomplete_submissions_removal_method=RemovalMethods.delete_permanently,
        )

        pending_submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.pending
        )
        in_progress_submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.in_progress
        )

        # Passing created_on to the factory create method does not work
        pending_delete_submission.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_delete_submission.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_delete_submission.save()
        pending_submission_to_be_anonymous.save()
        in_progress_delete_submission.save()
        in_progress_submission_to_be_anonymous.save()

        self._create_form_variables(pending_delete_submission.form)
        self._create_form_variables(in_progress_delete_submission.form)

        for submission in [
            not_successful,
            pending_too_recent,
            in_progress_too_recent,
            pending_delete_submission,
            pending_submission_to_be_anonymous,
            in_progress_delete_submission,
            in_progress_submission_to_be_anonymous,
        ]:
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )
            self._create_submission_variables(submission)

        make_sensitive_data_anonymous()

        not_successful.refresh_from_db()
        pending_too_recent.refresh_from_db()
        in_progress_too_recent.refresh_from_db()
        pending_delete_submission.refresh_from_db()
        pending_submission_to_be_anonymous.refresh_from_db()
        in_progress_delete_submission.refresh_from_db()
        in_progress_submission_to_be_anonymous.refresh_from_db()

        for submission in [
            not_successful,
            pending_too_recent,
            in_progress_too_recent,
            pending_delete_submission,
            in_progress_delete_submission,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        for submission in [
            in_progress_submission_to_be_anonymous,
            pending_submission_to_be_anonymous,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )
                self.assertTrue(submission._is_cleaned)

    def test_form_override_of_certain_incomplete_submissions_have_sensitive_data_removed(
        self,
    ):
        config = GlobalConfiguration.get_solo()

        override_form = FormFactory.create(
            incomplete_submissions_removal_method=RemovalMethods.make_anonymous,
            incomplete_submissions_removal_limit=config.incomplete_submissions_removal_limit
            + 7,
        )

        pending_override_submission = SubmissionFactory.create(
            form=override_form, registration_status=RegistrationStatuses.pending
        )
        in_progress_override_submission = SubmissionFactory.create(
            form=override_form, registration_status=RegistrationStatuses.in_progress
        )

        # Not pending or in_progress
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        pending_too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending, form=self.form
        )
        in_progress_too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress, form=self.form
        )

        pending_delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending,
            form__incomplete_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        in_progress_delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.in_progress,
            form__incomplete_submissions_removal_method=RemovalMethods.delete_permanently,
        )

        pending_submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.pending
        )
        in_progress_submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.in_progress
        )

        # Passing created_on to the factory create method does not work
        pending_delete_submission.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_delete_submission.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        in_progress_submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.incomplete_submissions_removal_limit + 1
        )
        pending_delete_submission.save()
        pending_submission_to_be_anonymous.save()
        in_progress_delete_submission.save()
        in_progress_submission_to_be_anonymous.save()

        self._create_form_variables(override_form)
        self._create_form_variables(pending_delete_submission.form)
        self._create_form_variables(in_progress_delete_submission.form)

        for submission in [
            not_successful,
            pending_too_recent,
            in_progress_too_recent,
            pending_delete_submission,
            pending_submission_to_be_anonymous,
            in_progress_delete_submission,
            in_progress_submission_to_be_anonymous,
            pending_override_submission,
            in_progress_override_submission,
        ]:
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )
            self._create_submission_variables(submission)

        make_sensitive_data_anonymous()

        not_successful.refresh_from_db()
        pending_too_recent.refresh_from_db()
        in_progress_too_recent.refresh_from_db()
        pending_delete_submission.refresh_from_db()
        pending_submission_to_be_anonymous.refresh_from_db()
        in_progress_delete_submission.refresh_from_db()
        in_progress_submission_to_be_anonymous.refresh_from_db()
        pending_override_submission.refresh_from_db()
        in_progress_override_submission.refresh_from_db()

        for submission in [
            not_successful,
            pending_too_recent,
            in_progress_too_recent,
            pending_delete_submission,
            in_progress_delete_submission,
            pending_override_submission,
            in_progress_override_submission,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        for submission in [
            in_progress_submission_to_be_anonymous,
            pending_submission_to_be_anonymous,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )
                self.assertTrue(submission._is_cleaned)

    def test_certain_errored_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        # Not failed
        not_failed = SubmissionFactory.create(
            registration_status=RegistrationStatuses.success, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )

        delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed,
            form__errored_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.failed
        )

        # Passing created_on to the factory create method does not work
        delete_submission.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        delete_submission.save()
        submission_to_be_anonymous.save()

        self._create_form_variables(delete_submission.form)

        for submission in [
            not_failed,
            too_recent,
            delete_submission,
            submission_to_be_anonymous,
        ]:
            SubmissionStepFactory.create_with_variables(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create_with_variables(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )

        make_sensitive_data_anonymous()

        not_failed.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [not_failed, too_recent, delete_submission]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldSensitive"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldNotSensitive"
                ],
                "This is not sensitive",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldSensitive2"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldNotSensitive2"
                ],
                "This is also not sensitive",
            )
            self.assertTrue(submission_to_be_anonymous._is_cleaned)

    def test_form_override_of_errored_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        override_form = FormFactory.create(
            errored_submissions_removal_method=RemovalMethods.make_anonymous,
            errored_submissions_removal_limit=config.errored_submissions_removal_limit
            + 7,
        )

        override_submission = SubmissionFactory.create(
            form=override_form, registration_status=RegistrationStatuses.failed
        )

        # Not failed
        not_failed = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )

        delete_submission = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed,
            form__successful_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_status=RegistrationStatuses.failed
        )

        # Passing created_on to the factory create method does not work
        delete_submission.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        override_submission.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        submission_to_be_anonymous.created_on = timezone.now() - timedelta(
            days=config.errored_submissions_removal_limit + 1
        )
        delete_submission.save()
        submission_to_be_anonymous.save()

        self._create_form_variables(override_form)
        self._create_form_variables(delete_submission.form)

        for submission in [
            not_failed,
            too_recent,
            delete_submission,
            submission_to_be_anonymous,
            override_submission,
        ]:
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive": "This is sensitive",
                    "textFieldNotSensitive": "This is not sensitive",
                },
                form_step=submission.form.formstep_set.all()[0],
                submission=submission,
            )
            SubmissionStepFactory.create(
                data={
                    "textFieldSensitive2": "This is also sensitive",
                    "textFieldNotSensitive2": "This is also not sensitive",
                },
                form_step=submission.form.formstep_set.all()[1],
                submission=submission,
            )
            self._create_submission_variables(submission)

        make_sensitive_data_anonymous()

        not_failed.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [
            not_failed,
            too_recent,
            delete_submission,
            override_submission,
        ]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldSensitive"],
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.first().data["textFieldNotSensitive"],
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldSensitive2"],
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionstep_set.last().data["textFieldNotSensitive2"],
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldSensitive"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.first().data[
                    "textFieldNotSensitive"
                ],
                "This is not sensitive",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldSensitive2"
                ],
                "",
            )
            self.assertEqual(
                submission_to_be_anonymous.submissionstep_set.last().data[
                    "textFieldNotSensitive2"
                ],
                "This is also not sensitive",
            )
            self.assertTrue(submission_to_be_anonymous._is_cleaned)
