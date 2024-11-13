from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time

from openforms.config.models import GlobalConfiguration
from openforms.forms.models.form_step import FormStep
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.constants import (
    RegistrationStatuses,
    SubmissionValueVariableSources,
)
from openforms.submissions.models import Submission, SubmissionValueVariable
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..constants import RemovalMethods
from ..tasks import delete_submissions, make_sensitive_data_anonymous


class DeleteSubmissionsTask(TestCase):
    def test_successful_submissions_correctly_deleted(self):
        config = GlobalConfiguration.get_solo()

        # Not successful
        SubmissionFactory.create(registration_status=RegistrationStatuses.failed)
        # Too recent
        SubmissionFactory.create(registration_success=True)

        anonymous_submission = SubmissionFactory.create(
            registration_success=True,
            form__successful_submissions_removal_method=RemovalMethods.make_anonymous,
        )
        submission_to_be_deleted = SubmissionFactory.create(registration_success=True)

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

    def test_successful_submissions_correctly_deleted_the_same_day_when_form_removal_limit_is_0(
        self,
    ):
        form = FormFactory.create(
            successful_submissions_removal_limit=0,
            incomplete_submissions_removal_limit=7,
            errored_submissions_removal_limit=7,
            all_submissions_removal_limit=7,
        )

        with freeze_time("2024-11-12T18:00:00+01:00"):
            # Submission not connected to form
            SubmissionFactory.create(registration_success=True)

            submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_success=True
            )

        self.assertEqual(Submission.objects.count(), 2)

        with freeze_time("2024-11-12T19:00:00+01:00"):
            delete_submissions()

        # Only the submission connected to the form should be deleted
        self.assertEqual(Submission.objects.count(), 1)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()

    @tag("gh-2632")
    def test_delete_successful_submission_with_deleted_form_step(self):
        config = GlobalConfiguration.get_solo()

        # submission to be deleted
        before_limit = timezone.now() - timedelta(
            days=config.successful_submissions_removal_limit + 1
        )
        with freeze_time(before_limit):
            sub = SubmissionFactory.create(completed=True)

        # create a form step to then delete which introduces the RecursionError
        form_step = FormStepFactory.create(form=sub.form)
        SubmissionStepFactory.create(submission=sub, form_step=form_step)

        # delete form step - this causes the recursion error
        form_step.delete()

        assert sub.submissionstep_set.count() == 1
        assert isinstance(sub.submissionstep_set.get().form_step, FormStep)
        assert not FormStep.objects.exists()

        delete_submissions()

        self.assertFalse(Submission.objects.exists())

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
            registration_success=True,
        )
        submission_anonymous = SubmissionFactory.create(
            form=form_make_anonymous,
            registration_success=True,
        )

        submission_to_be_deleted = SubmissionFactory.create(registration_success=True)
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
            in_progress_submission_to_be_deleted.refresh_from_db()

    def test_incomplete_submissions_correctly_deleted_the_same_day_when_form_removal_limit_is_0(
        self,
    ):
        form = FormFactory.create(
            successful_submissions_removal_limit=7,
            incomplete_submissions_removal_limit=0,
            errored_submissions_removal_limit=7,
            all_submissions_removal_limit=7,
        )

        with freeze_time("2024-11-12T18:00:00+01:00"):
            # Incomplete submissions not connected to the form
            SubmissionFactory.create(registration_status=RegistrationStatuses.pending)
            SubmissionFactory.create(
                registration_status=RegistrationStatuses.in_progress
            )

            SubmissionFactory.create(form=form, registration_success=True)
            pending_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.pending
            )
            in_progress_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.in_progress
            )

        self.assertEqual(Submission.objects.count(), 5)

        with freeze_time("2024-11-12T19:00:00+01:00"):
            delete_submissions()

        self.assertEqual(Submission.objects.count(), 3)
        with self.assertRaises(ObjectDoesNotExist):
            pending_submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            in_progress_submission_to_be_deleted.refresh_from_db()

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
        SubmissionFactory.create(registration_success=True)
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

    def test_failed_submissions_correctly_deleted_the_same_day_when_form_removal_limit_is_0(
        self,
    ):
        form = FormFactory.create(
            successful_submissions_removal_limit=7,
            incomplete_submissions_removal_limit=7,
            errored_submissions_removal_limit=0,
            all_submissions_removal_limit=7,
        )

        with freeze_time("2024-11-12T18:00:00+01:00"):
            # Failed submission not connected to the form
            SubmissionFactory.create(registration_status=RegistrationStatuses.failed)

            # Successful and incomplete submissions
            SubmissionFactory.create(form=form, registration_success=True)
            SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.pending
            )
            SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.in_progress
            )

            failed_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.failed
            )

        self.assertEqual(Submission.objects.count(), 5)

        with freeze_time("2024-11-12T19:00:00+01:00"):
            delete_submissions()

        self.assertEqual(Submission.objects.count(), 4)
        with self.assertRaises(ObjectDoesNotExist):
            failed_submission_to_be_deleted.refresh_from_db()

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

    def test_all_submissions_correctly_deleted_the_same_day_when_form_removal_limit_is_0(
        self,
    ):
        form = FormFactory.create(
            successful_submissions_removal_limit=7,
            incomplete_submissions_removal_limit=7,
            errored_submissions_removal_limit=7,
            all_submissions_removal_limit=0,
        )

        with freeze_time("2024-11-12T18:00:00+01:00"):
            # Submissions not connected to the form
            SubmissionFactory.create(registration_success=True)
            SubmissionFactory.create(registration_status=RegistrationStatuses.pending)
            SubmissionFactory.create(
                registration_status=RegistrationStatuses.in_progress
            )
            SubmissionFactory.create(registration_status=RegistrationStatuses.failed)

            submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_success=True
            )
            pending_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.pending
            )
            in_progress_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.in_progress
            )
            failed_submission_to_be_deleted = SubmissionFactory.create(
                form=form, registration_status=RegistrationStatuses.failed
            )

        self.assertEqual(Submission.objects.count(), 8)

        with freeze_time("2024-11-12T19:00:00+01:00"):
            delete_submissions()

        self.assertEqual(Submission.objects.count(), 4)
        with self.assertRaises(ObjectDoesNotExist):
            submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            pending_submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            in_progress_submission_to_be_deleted.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            failed_submission_to_be_deleted.refresh_from_db()

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
                ],
            }
        )
        cls.form_definition_2 = FormDefinitionFactory.create(
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

    def _add_form_steps(self, form):
        if not form.formstep_set.exists():
            # Creates also the form variables
            FormStepFactory.create(form=form, form_definition=self.form_definition)
            FormStepFactory.create(form=form, form_definition=self.form_definition_2)

    def test_certain_successful_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        # Not successful
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(registration_success=True, form=self.form)

        delete_submission = SubmissionFactory.create(
            registration_success=True,
            form__successful_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_success=True
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

        self._add_form_steps(delete_submission.form)

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

        make_sensitive_data_anonymous()

        not_successful.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [not_successful, too_recent, delete_submission]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive", submission=submission
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive2", submission=submission
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            sensitive_variable1 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable1.value,
                "",
            )
            self.assertEqual(
                sensitive_variable1.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive", submission=submission_to_be_anonymous
                ).value,
                "This is not sensitive",
            )
            sensitive_variable2 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive2", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable2.value,
                "",
            )
            self.assertEqual(
                sensitive_variable2.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive2", submission=submission_to_be_anonymous
                ).value,
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
            form=override_form, registration_success=True
        )

        # Not successful
        not_successful = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, form=self.form
        )
        # Too recent
        too_recent = SubmissionFactory.create(registration_success=True, form=self.form)

        delete_submission = SubmissionFactory.create(
            registration_success=True,
            form__successful_submissions_removal_method=RemovalMethods.delete_permanently,
        )
        submission_to_be_anonymous = SubmissionFactory.create(
            form=self.form, registration_success=True
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

        self._add_form_steps(override_form)
        self._add_form_steps(delete_submission.form)

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
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive", submission=submission
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive2", submission=submission
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            sensitive_variable1 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable1.value,
                "",
            )
            self.assertEqual(
                sensitive_variable1.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive", submission=submission_to_be_anonymous
                ).value,
                "This is not sensitive",
            )
            sensitive_variable2 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive2", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable2.value,
                "",
            )
            self.assertEqual(
                sensitive_variable2.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive2", submission=submission_to_be_anonymous
                ).value,
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

        self._add_form_steps(pending_delete_submission.form)
        self._add_form_steps(in_progress_delete_submission.form)

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
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive", submission=submission
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive2", submission=submission
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )

        for submission in [
            in_progress_submission_to_be_anonymous,
            pending_submission_to_be_anonymous,
        ]:
            with self.subTest(submission=submission):
                sensitive_variable1 = SubmissionValueVariable.objects.get(
                    key="textFieldSensitive", submission=submission
                )
                self.assertEqual(
                    sensitive_variable1.value,
                    "",
                )
                self.assertEqual(
                    sensitive_variable1.source,
                    SubmissionValueVariableSources.sensitive_data_cleaner,
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                sensitive_variable2 = SubmissionValueVariable.objects.get(
                    key="textFieldSensitive2", submission=submission
                )
                self.assertEqual(
                    sensitive_variable2.value,
                    "",
                )
                self.assertEqual(
                    sensitive_variable2.source,
                    SubmissionValueVariableSources.sensitive_data_cleaner,
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
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

        self._add_form_steps(override_form)
        self._add_form_steps(pending_delete_submission.form)
        self._add_form_steps(in_progress_delete_submission.form)

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
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive", submission=submission
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive2", submission=submission
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )

        for submission in [
            in_progress_submission_to_be_anonymous,
            pending_submission_to_be_anonymous,
        ]:
            with self.subTest(submission=submission):
                sensitive_variable1 = SubmissionValueVariable.objects.get(
                    key="textFieldSensitive", submission=submission
                )
                self.assertEqual(
                    sensitive_variable1.value,
                    "",
                )
                self.assertEqual(
                    sensitive_variable1.source,
                    SubmissionValueVariableSources.sensitive_data_cleaner,
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                sensitive_variable2 = SubmissionValueVariable.objects.get(
                    key="textFieldSensitive2", submission=submission
                )
                self.assertEqual(
                    sensitive_variable2.value,
                    "",
                )
                self.assertEqual(
                    sensitive_variable2.source,
                    SubmissionValueVariableSources.sensitive_data_cleaner,
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )
                self.assertTrue(submission._is_cleaned)

    def test_certain_errored_submissions_have_sensitive_data_removed(self):
        config = GlobalConfiguration.get_solo()

        # Not failed
        not_failed = SubmissionFactory.create(registration_success=True, form=self.form)
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

        self._add_form_steps(delete_submission.form)

        for submission in [
            not_failed,
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

        make_sensitive_data_anonymous()

        not_failed.refresh_from_db()
        too_recent.refresh_from_db()
        delete_submission.refresh_from_db()
        submission_to_be_anonymous.refresh_from_db()

        for submission in [not_failed, too_recent, delete_submission]:
            with self.subTest(submission=submission):
                self.assertEqual(
                    submission.submissionvaluevariable_set.get(
                        key="textFieldSensitive"
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    submission.submissionvaluevariable_set.get(
                        key="textFieldNotSensitive"
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    submission.submissionvaluevariable_set.get(
                        key="textFieldSensitive2"
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    submission.submissionvaluevariable_set.get(
                        key="textFieldNotSensitive2"
                    ).value,
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            sensitive_variable1 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable1.value,
                "",
            )
            self.assertEqual(
                sensitive_variable1.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive", submission=submission_to_be_anonymous
                ).value,
                "This is not sensitive",
            )
            sensitive_variable2 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive2", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable2.value,
                "",
            )
            self.assertEqual(
                sensitive_variable2.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive2", submission=submission_to_be_anonymous
                ).value,
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

        self._add_form_steps(override_form)
        self._add_form_steps(delete_submission.form)

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
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive", submission=submission
                    ).value,
                    "This is sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive", submission=submission
                    ).value,
                    "This is not sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldSensitive2", submission=submission
                    ).value,
                    "This is also sensitive",
                )
                self.assertEqual(
                    SubmissionValueVariable.objects.get(
                        key="textFieldNotSensitive2", submission=submission
                    ).value,
                    "This is also not sensitive",
                )

        with self.subTest(submission=submission_to_be_anonymous):
            sensitive_variable1 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable1.value,
                "",
            )
            self.assertEqual(
                sensitive_variable1.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive", submission=submission_to_be_anonymous
                ).value,
                "This is not sensitive",
            )
            sensitive_variable2 = SubmissionValueVariable.objects.get(
                key="textFieldSensitive2", submission=submission_to_be_anonymous
            )
            self.assertEqual(
                sensitive_variable2.value,
                "",
            )
            self.assertEqual(
                sensitive_variable2.source,
                SubmissionValueVariableSources.sensitive_data_cleaner,
            )
            self.assertEqual(
                SubmissionValueVariable.objects.get(
                    key="textFieldNotSensitive2", submission=submission_to_be_anonymous
                ).value,
                "This is also not sensitive",
            )
            self.assertTrue(submission_to_be_anonymous._is_cleaned)
