from django.test import TestCase
from django.utils.translation import gettext as _

from openforms.forms.models import FormLogic
from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import VariablesTestMixin


class EventTests(VariablesTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.from_data(
            {
                "firstname": "foo",
                "birthdate": "2022-06-20",
            },
        )

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

        json_logic_trigger = {
            ">": [{"date": {"var": "birthdate"}}, {"date": "2022-06-20"}]
        }

        json_logic_trigger_2 = {"==": [{"var": "firstname"}, "bar"]}

        actions = [
            {
                "component": "firstname",
                "formStep": "",
                "action": {
                    "type": "property",
                    "property": {"value": "disabled", "type": "bool"},
                    "state": True,
                },
            }
        ]

        actions_2 = [
            {
                "component": "",
                "formStep": "",
                "action": {
                    "type": "disable-next",
                    "property": {"type": "", "value": ""},
                    "value": "",
                    "state": "",
                },
            }
        ]

        actual = self.submission.get_merged_data()
        expected = {"firstname": "foo", "birthdate": "2022-06-20"}
        rule = FormLogic(
            form=self.submission.form,
            json_logic_trigger=json_logic_trigger,
            actions=actions,
        )
        rule_2 = FormLogic(
            form=self.submission.form,
            json_logic_trigger=json_logic_trigger_2,
            actions=actions_2,
        )

        logevent.submission_logic_evaluated(
            self.submission,
            [{"rule": rule, "trigger": True}, {"rule": rule_2, "trigger": False}],
        )
        logs = self.submission.logs.all()
        log = logs.last()
        logged_rules = log.extra_data["log_evaluated_rules"]

        self.assertEquals(1, logs.count())
        self.assertEquals(2, len(logged_rules))
        self.assertEquals(actual, expected)
