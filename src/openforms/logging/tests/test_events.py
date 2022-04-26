from django.test import TestCase
from django.utils.translation import gettext as _

from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory


class EventTests(TestCase):
    # test for specific events
    def test_submission_start(self):
        with self.subTest("anon"):
            submission = SubmissionFactory.create()
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(_("Anonymous user"), log.fmt_user)

        with self.subTest("auth bsn"):
            submission = SubmissionFactory.create(auth_plugin="mock", bsn="123456789")
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(
                _("Authenticated via plugin {auth}").format(auth="mock (bsn)"),
                log.fmt_user,
            )

        with self.subTest("bsn but no auth"):
            # Github #1467
            submission = SubmissionFactory.create(bsn="123456789")
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(_("Anonymous user"), log.fmt_user)
