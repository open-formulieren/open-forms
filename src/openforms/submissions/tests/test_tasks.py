from datetime import timedelta
from unittest import TestCase

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from openforms.config.constants import RemovalMethods
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission
from openforms.submissions.tasks import delete_submissions
from openforms.submissions.tests.factories import SubmissionFactory


class DeleteSubmissionsTask(TestCase):
    def setUp(self) -> None:
        Submission.objects.all().delete()

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
