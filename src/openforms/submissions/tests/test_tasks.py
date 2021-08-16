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

    def test_form_settings_override_global_configuration(self):
        config = GlobalConfiguration.get_solo()
        form_longer_limit = FormFactory.create(
            successful_submissions_removal_limit=config.successful_submissions_removal_limit
            + 7
        )
        form_make_anonymous = FormFactory.create(
            successful_submissions_removal_method=RemovalMethods.make_anonymous
        )

        submission_longer_limit = SubmissionFactory.create(form=form_longer_limit)
        submission_anonymous = SubmissionFactory.create(form=form_make_anonymous)

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
