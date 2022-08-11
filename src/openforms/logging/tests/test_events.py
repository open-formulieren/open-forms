from django.test import TestCase
from django.utils.translation import gettext as _

from openforms.forms.tests.factories import FormLogicFactory
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

    def test_submission_logic_evaluated(self):

        submission = SubmissionFactory.from_data(
            {
                "firstname": "foo",
                "birthdate": "2022-06-20",
            },
        )

        json_logic_trigger = {
            ">": [{"date": {"var": "birthdate"}}, {"date": "2022-06-20"}]
        }

        json_logic_trigger_2 = {"==": [{"var": "firstname"}, "bar"]}

        rule = FormLogicFactory(
            form=submission.form,
            json_logic_trigger=json_logic_trigger,
            actions=[],
        )
        rule_2 = FormLogicFactory(
            form=submission.form,
            json_logic_trigger=json_logic_trigger_2,
            actions=[],
        )

        logevent.submission_logic_evaluated(
            submission,
            [{"rule": rule, "trigger": True}, {"rule": rule_2, "trigger": False}],
            submission.data,
        )

        log = TimelineLogProxy.objects.get(object_id=submission.id)
        logged_rules = log.extra_data["evaluated_rules"]

        self.assertEqual(2, len(logged_rules))
        self.assertEqual(
            {
                "raw_logic_expression": json_logic_trigger,
                "trigger": True,
                "readable_rule": "birthdate > 2022-06-20",
                "targeted_components": rule.actions,
            },
            logged_rules[0],
        )
        self.assertEqual(
            {
                "raw_logic_expression": json_logic_trigger_2,
                "trigger": False,
                "readable_rule": "firstname == bar",
                "targeted_components": rule_2.actions,
            },
            logged_rules[1],
        )
