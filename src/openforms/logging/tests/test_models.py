from django.test import TestCase
from django.utils.translation import gettext as _

from freezegun import freeze_time

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory
from openforms.logging.tests.base import LoggingTestMixin
from openforms.logging.tests.factories import TimelineLogProxyFactory
from openforms.submissions.tests.factories import SubmissionFactory


class TimelineLogProxyTests(TestCase):
    def test_is_submission(self):
        log = TimelineLogProxyFactory.create(content_object=None)
        self.assertFalse(log.is_submission)

        submission = SubmissionFactory.create()
        log = TimelineLogProxyFactory.create(content_object=submission)
        self.assertTrue(log.is_submission)

    def test_is_form(self):
        log = TimelineLogProxyFactory.create(content_object=None)
        self.assertFalse(log.is_form)

        form = FormFactory.create()
        log = TimelineLogProxyFactory.create(content_object=form)
        self.assertTrue(log.is_form)

    def test_get_formatted_fields(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email"},
                {
                    "key": "theBSN",
                    "label": "The BSN",
                    "prefill": {
                        "attribute": "bsn"
                    },
                    "components": [{
                        "key": "theFirstName",
                        "label": "The First Name",
                        "prefill": {
                            "attribute": "voornamen"
                        }
                    }]
                },
            ]
        )
        fields = ["bsn", "voornamen"]
        log = TimelineLogProxyFactory.create(
            content_object=submission,
            user=UserFactory(username="Bob"),
            extra_data={"plugin_id": "myplugin", "plugin_label": "MyPlugin", "fields": fields},
        )
        self.assertEqual(log.get_formatted_fields(fields), ['The BSN (bsn)', 'The First Name (voornamen)'])

    def test_format_fields(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "label": "Email"},
                {
                    "key": "theBSN",
                    "label": "The BSN",
                    "prefill": {
                        "attribute": "bsn"
                    },
                    "components": [{
                        "key": "theFirstName",
                        "label": "The First Name",
                        "prefill": {
                            "attribute": "voornamen"
                        }
                    }]
                },
            ]
        )
        log = TimelineLogProxyFactory.create(
            content_object=submission,
            user=UserFactory(username="Bob"),
            extra_data={"plugin_id": "myplugin", "plugin_label": "MyPlugin", "fields": ["bsn", "voornamen"]},
        )
        self.assertEqual(log.fmt_fields, 'The BSN (bsn), The First Name (voornamen)')

    @freeze_time("2020-01-02 12:34:00")
    def test_format_accessors(self):
        submission = SubmissionFactory.create(form__name="MyForm")
        log = TimelineLogProxyFactory.create(
            content_object=submission,
            user=UserFactory(username="Bob"),
            extra_data={"plugin_id": "myplugin", "plugin_label": "MyPlugin"},
        )
        self.assertEqual(
            f"[2020-01-02 13:34:00 CET] (Submission {submission.id})", log.fmt_lead
        )
        self.assertEqual(f'"MyForm" (ID: {submission.form.id})', log.fmt_form)
        self.assertEqual(_("User") + ' "Bob"', log.fmt_user)
        self.assertEqual('"MyPlugin" (myplugin)', log.fmt_plugin)

        # fallbacks
        log = TimelineLogProxyFactory.create(content_object=None, user=None)
        self.assertEqual(_("Anonymous user"), log.fmt_user)
        self.assertEqual(f"[2020-01-02 13:34:00 CET]", log.fmt_lead)
        self.assertEqual(_("(unknown)"), log.fmt_plugin)


class LoggingTestMixinTest(LoggingTestMixin, TestCase):
    def test_assertLogExtraDataEquals(self):
        log = TimelineLogProxyFactory.create(extra_data={"foo": "good"})
        self.assertLogExtraDataEquals(log, foo="good")
        with self.assertRaises(AssertionError):
            self.assertLogExtraDataEquals(log, foo="bad")

    def test_assertLogEventLast(self):
        TimelineLogProxyFactory.create(
            extra_data={"log_event": "foo_event", "foo": "good"}
        )
        self.assertLogEventLast("foo_event")
        self.assertLogEventLast("foo_event", foo="good")
        with self.assertRaises(AssertionError):
            self.assertLogEventLast("bar_event")
        with self.assertRaises(AssertionError):
            self.assertLogEventLast("foo_event", foo="bad")
