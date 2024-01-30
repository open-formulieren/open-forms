import datetime
from unittest.mock import patch

from django.utils import timezone

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.constants import PostSubmissionEvents
from openforms.submissions.tasks import retry_processing_submissions
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..models.form_statistics import FormStatistics


class FormStatisticsTests(SubmissionsMixin, APITestCase):
    @freeze_time("2020-12-11T12:00:00+00:00")
    def test_form_statistics_is_created(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        form_statistics = FormStatistics.objects.get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(form_statistics.form, form)
        self.assertEqual(form_statistics.form_name, form.name)
        self.assertEqual(form_statistics.submission_count, 1)
        self.assertEqual(form_statistics.first_submission, timezone.now())
        self.assertEqual(form_statistics.last_submission, timezone.now())

    def test_form_statistics_is_updated(self):
        with freeze_time("2020-12-11T12:00:00+00:00") as frozen_datetime:
            form = FormFactory.create()

            # assuming that the form has been already submitted at least one time
            FormStatistics.objects.create(
                form=form,
                form_name=form.name,
                submission_count=1,
                last_submission=datetime.datetime(
                    2020, 12, 11, 12, 00, 00, tzinfo=datetime.timezone.utc
                ),
            )

            submission = SubmissionFactory.create(form=form)
            self._add_submission_to_session(submission)

            # submit the form for the second time after 1 minute
            frozen_datetime.tick(delta=datetime.timedelta(minutes=1))

            endpoint = reverse(
                "api:submission-complete", kwargs={"uuid": submission.uuid}
            )

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(endpoint, {"privacy_policy_accepted": True})

            form_statistics = FormStatistics.objects.get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(form_statistics.form, form)
        self.assertEqual(form_statistics.form_name, form.name)
        self.assertEqual(form_statistics.submission_count, 2)
        self.assertEqual(
            form_statistics.first_submission,
            datetime.datetime(2020, 12, 11, 12, 00, 00, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            form_statistics.last_submission,
            datetime.datetime(2020, 12, 11, 12, 1, 00, tzinfo=datetime.timezone.utc),
        )

    @patch("openforms.submissions.tasks.on_post_submission_event")
    def test_resend_submission_task_does_not_affect_counter(self, m):
        with freeze_time("2020-12-11T12:00:00+00:00") as frozen_datetime:
            form = FormFactory.create()

            FormStatistics.objects.create(
                form=form,
                form_name=form.name,
                submission_count=1,
                last_submission=datetime.datetime(
                    2020, 12, 11, 12, 00, 00, tzinfo=datetime.timezone.utc
                ),
            )
            failed_submission = SubmissionFactory.create(
                registration_failed=True,
                needs_on_completion_retry=True,
                completed_on=datetime.datetime(
                    2020, 12, 11, 12, 00, 00, tzinfo=datetime.timezone.utc
                ),
                form=form,
            )

            frozen_datetime.tick(delta=datetime.timedelta(minutes=10))
            retry_processing_submissions()

            form_statistics = FormStatistics.objects.get()

        self.assertEqual(m.call_count, 1)
        m.assert_called_once_with(failed_submission.id, PostSubmissionEvents.on_retry)

        self.assertEqual(form_statistics.form, form)
        self.assertEqual(form_statistics.submission_count, 1)
