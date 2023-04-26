from typing import cast

from django.test import TestCase, override_settings
from django.utils.translation import gettext as _

from openforms.forms.models import FormLogic
from openforms.forms.tests.factories import FormLogicFactory
from openforms.logging import logevent, logic
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.logic.rules import EvaluatedRule
from openforms.submissions.tests.factories import SubmissionFactory


class EventTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        TimelineLogProxy.objects.all().delete()

    # test for specific events
    def test_submission_start(self):
        with self.subTest("anon"):
            submission = SubmissionFactory.create()
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(_("Anonymous user"), log.fmt_user)

        with self.subTest("auth bsn"):
            submission = SubmissionFactory.create(
                auth_info__value="123456789", auth_info__plugin="mock"
            )
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(
                _("Authenticated via plugin {auth}").format(auth="mock (bsn)"),
                log.fmt_user,
            )

        with self.subTest("No auth"):
            # Github #1467
            submission = SubmissionFactory.create()
            logevent.submission_start(submission)

            log = TimelineLogProxy.objects.last()
            self.assertEqual(_("Anonymous user"), log.fmt_user)

    @override_settings(LANGUAGE_CODE="en")
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
        rule = cast(FormLogic, rule)
        rule_2 = FormLogicFactory(
            form=submission.form,
            json_logic_trigger=json_logic_trigger_2,
            actions=[],
        )
        rule_2 = cast(FormLogic, rule_2)

        logic.log_logic_evaluation(
            submission,
            [
                EvaluatedRule(rule=rule, triggered=True),
                EvaluatedRule(rule=rule_2, triggered=False),
            ],
            submission.data,
            submission.data,
        )

        log = TimelineLogProxy.objects.get(object_id=submission.id)
        logged_rules = log.extra_data["evaluated_rules"]

        self.assertEqual(2, len(logged_rules))
        self.assertEqual(
            {
                "raw_logic_expression": json_logic_trigger,
                "trigger": True,
                "readable_rule": r"date({{birthdate}}) is greater than date('2022-06-20')",
                "targeted_components": rule.actions,
            },
            logged_rules[0],
        )
        self.assertEqual(
            {
                "raw_logic_expression": json_logic_trigger_2,
                "trigger": False,
                "readable_rule": r"{{firstname}} is equal to 'bar'",
                "targeted_components": rule_2.actions,
            },
            logged_rules[1],
        )
