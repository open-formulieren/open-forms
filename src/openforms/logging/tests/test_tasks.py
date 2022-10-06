from django.test import TestCase
from django.utils import timezone

from openforms.logging.models import TimelineLogProxy
from openforms.logging.tasks import log_logic_evaluation
from openforms.submissions.tests.factories import SubmissionFactory


class TestLogTask(TestCase):
    def test_no_logged_rules(self):
        submission = SubmissionFactory.create()
        timestamp = timezone.now().isoformat()

        log_logic_evaluation(
            submission_id=submission.id,
            timestamp=timestamp,
            evaluated_rules=[],
            initial_data=submission.data,
            resolved_data=submission.data,
        )

        self.assertEqual(0, TimelineLogProxy.objects.count())
