"""
Test the registration hook on submissions.
"""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, tag
from django.utils import timezone

from freezegun import freeze_time
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.config.models import GlobalConfiguration
from openforms.forms.models import FormRegistrationBackend
from openforms.logging.models import TimelineLogProxy
from openforms.payments.constants import PaymentStatus
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.logging import ensure_logger_level

from ..base import BasePlugin
from ..exceptions import RegistrationFailed
from ..registry import Registry
from ..tasks import register_submission
from .utils import patch_registry


class OptionsSerializer(serializers.Serializer):
    string = serializers.CharField()
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())


class ResultSerializer(serializers.Serializer):
    external_id = serializers.UUIDField()


class RegistrationHookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )

        cls.submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="callback",
            form__registration_backend_options={
                "string": "some-option",
                "service": cls.service.id,
            },
        )

    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_assertion_plugin_with_deserialized_options(self):
        register = Registry()

        # register the callback, including the assertions
        test_closure = self

        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Assertion callback"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                test_closure.assertEqual(submission, test_closure.submission)
                test_closure.assertIsInstance(options, dict)
                test_closure.assertEqual(options["string"], "some-option")
                test_closure.assertEqual(options["service"], test_closure.service)

                return {"result": "ok"}

        # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            register_submission(self.submission.id, PostSubmissionEvents.on_completion)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.success
        )
        self.assertEqual(
            self.submission.registration_result,
            {"result": "ok"},
        )
        self.assertEqual(self.submission.last_register_date, timezone.now())

    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_failing_registration(self):
        register = Registry()

        # register the callback, including the assertions
        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Assertion callback"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                err = ZeroDivisionError("Can't divide by zero")
                raise RegistrationFailed("zerodiv") from err

        # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with (
            self.subTest("On completion - does NOT raise"),
            patch_registry(model_field, register),
            self.assertLogs(level="WARNING") as log,
        ):
            register_submission(self.submission.id, PostSubmissionEvents.on_completion)

            # check we log a WARNING with stack
            error_log = log.records[-1]
            self.assertEqual(error_log.levelname, "WARNING")
            self.assertIn("failed", error_log.message)
            self.assertIsNotNone(error_log.exc_info)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        self.assertTrue(self.submission.needs_on_completion_retry)
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Can't divide by zero", tb)
        self.assertEqual(self.submission.last_register_date, timezone.now())

        with (
            self.subTest("On retry - does raise"),
            patch_registry(model_field, register),
            self.assertRaises(RegistrationFailed),
        ):
            register_submission(self.submission.id, PostSubmissionEvents.on_retry)

    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_failing_registration_with_bugged_plugin(self):
        register = Registry()

        # register the callback, including the assertions
        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Assertion callback"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                # plugin errors with unexected exception (= not converted into RegistrationFailed)
                raise ZeroDivisionError("Can't divide by zero")

        # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with (
            self.subTest("On completion - does NOT raise"),
            patch_registry(model_field, register),
            self.assertLogs(level="ERROR") as log,
        ):
            register_submission(self.submission.id, PostSubmissionEvents.on_completion)

            # check we log an ERROR with stack
            error_log = log.records[-1]
            self.assertEqual(error_log.levelname, "ERROR")
            self.assertIn("unexpectedly errored", error_log.message)
            self.assertIsNotNone(error_log.exc_info)

        self.submission.refresh_from_db()
        self.assertTrue(self.submission.needs_on_completion_retry)
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Can't divide by zero", tb)
        self.assertEqual(self.submission.last_register_date, timezone.now())

        with (
            self.subTest("On retry - does raise"),
            patch_registry(model_field, register),
            self.assertRaises(ZeroDivisionError),
        ):
            register_submission(self.submission.id, PostSubmissionEvents.on_retry)

    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_retrying_registration_already_succeeded_just_returns(self):
        register = Registry()

        # register the callback, including the assertions
        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Assertion callback"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                err = ZeroDivisionError("Can't divide by zero")
                raise RegistrationFailed("zerodiv") from err

        # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")

        last_register_date = timezone.now() - timedelta(hours=1)
        submission = SubmissionFactory.create(
            last_register_date=last_register_date,
            registration_success=True,
            form__registration_backend="callback",
            form__registration_backend_options={
                "string": "some-option",
                "service": self.service.id,
            },
        )

        with patch_registry(model_field, register):
            # Assert task just returns
            self.assertIsNone(
                register_submission(submission.id, PostSubmissionEvents.on_completion)
            )

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)
        self.assertEqual(submission.last_register_date, last_register_date)

    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_submission_marked_complete_when_form_has_no_registration_backend(self):
        submission_no_registration_backend = SubmissionFactory.create(
            completed=True,
            form__registration_backend="",
            form__registration_backend_options={},
        )

        # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, Registry()):
            register_submission(
                submission_no_registration_backend.id,
                PostSubmissionEvents.on_completion,
            )

        submission_no_registration_backend.refresh_from_db()
        self.assertEqual(
            submission_no_registration_backend.registration_status,
            RegistrationStatuses.success,
        )
        self.assertIsNone(
            submission_no_registration_backend.registration_result,
        )
        self.assertEqual(
            submission_no_registration_backend.last_register_date, timezone.now()
        )

    def test_submission_is_not_completed_yet(self):
        submission = SubmissionFactory.create(completed=False)

        with self.assertLogs() as logs:
            register_submission(submission.id, PostSubmissionEvents.on_completion)

        self.assertEqual(
            logs.records[0].msg,
            "Trying to register submission '%s' which is not completed.",
        )

    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    @freeze_time("2021-08-04T12:00:00+02:00")
    def test_registration_plugin_not_enabled(self, mock_get_solo):
        register = Registry()

        # register the callback
        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Callback"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                pass

        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"registrations": {"callback": {"enabled": False}}}
        )

        # # call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            with self.subTest("on completion"):
                register_submission(
                    self.submission.id, PostSubmissionEvents.on_completion
                )

            with self.subTest("on retry"):
                with (
                    ensure_logger_level("DEBUG"),
                    self.assertRaises(RegistrationFailed),
                    self.assertLogs(level="DEBUG") as logs,
                ):
                    register_submission(
                        self.submission.id, PostSubmissionEvents.on_retry
                    )

        self.assertEqual(logs.records[-1].msg, "Plugin '%s' is not enabled")

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        self.assertTrue(self.submission.needs_on_completion_retry)
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Registration plugin is not enabled", tb)
        self.assertEqual(self.submission.last_register_date, timezone.now())

    def test_registration_backend_invalid_options(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="email",
            form__registration_backend_options={},
        )  # Missing "to_emails" option

        with (
            self.subTest("On completion - does NOT raise"),
            self.assertLogs(level="WARNING") as logs,
        ):
            register_submission(submission.id, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()

            self.assertIn(
                "Registration using plugin '%r' for submission '%s' failed",
                logs.records[-1].msg,
            )
            self.assertTrue(submission.needs_on_completion_retry)

        with (
            self.subTest("On retry - does raise"),
            self.assertRaises(ValidationError),
        ):
            register_submission(submission.id, PostSubmissionEvents.on_retry)

    def test_calling_registration_task_with_serialized_args(self):
        submission = SubmissionFactory.create(
            completed=True,
            with_public_registration_reference=True,
            with_completed_payment=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["registration@test.nl"]},
        )

        with patch(
            "openforms.registrations.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(wait_for_payment_to_register=True),
        ):
            register_submission(
                submission.id, str(PostSubmissionEvents.on_payment_complete)
            )

        submission.refresh_from_db()

        self.assertEqual(submission.registration_status, RegistrationStatuses.success)

    @tag("gh-4425")
    def test_registration_hook_with_failed_and_completed_payments(self):
        submission = SubmissionFactory.create(
            completed=True,
            with_public_registration_reference=True,
            with_failed_payment=True,
            with_completed_payment=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["registration@test.nl"]},
        )
        assert submission.payments.count() == 2
        with patch(
            "openforms.registrations.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(wait_for_payment_to_register=True),
        ):
            register_submission(
                submission.id, str(PostSubmissionEvents.on_payment_complete)
            )

        registered_payments = submission.payments.filter(
            status=PaymentStatus.registered
        )
        self.assertEqual(registered_payments.count(), 1)
        failed_payments = submission.payments.filter(status=PaymentStatus.failed)
        self.assertEqual(failed_payments.count(), 1)


class NumRegistrationsTest(TestCase):
    @patch("openforms.plugins.plugin.GlobalConfiguration.get_solo")
    def test_limit_registration_attempts(self, mock_get_solo):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="callback",
        )

        register = Registry()

        TEST_NUM_ATTEMPTS = 3

        # register the callback
        @register("callback")
        class FailsPlugin(BasePlugin):
            verbose_name = "Callback"
            configuration_options = serializers.Serializer

            def register_submission(self, submission, options):
                raise RegistrationFailed("fake failure")

        mock_get_solo.return_value = GlobalConfiguration(
            registration_attempt_limit=TEST_NUM_ATTEMPTS,
            plugin_configuration={"registrations": {"callback": {"enabled": True}}},
        )

        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            # first registration won't re-raise RegistrationFailed
            register_submission(submission.id, PostSubmissionEvents.on_completion)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            self.assertEqual(submission.registration_attempts, 1)
            # marked for retry
            self.assertTrue(submission.needs_on_completion_retry)

            # second and next attempts will re-raise RegistrationFailed for Celery retry
            for i in range(2, TEST_NUM_ATTEMPTS + 1):
                with self.assertRaises(RegistrationFailed):
                    register_submission(submission.id, PostSubmissionEvents.on_retry)

                submission.refresh_from_db()
                self.assertEqual(
                    submission.registration_status, RegistrationStatuses.failed
                )
                self.assertEqual(submission.registration_attempts, i)
                # marked for retry
                self.assertTrue(submission.needs_on_completion_retry)

            # check
            self.assertEqual(submission.registration_attempts, TEST_NUM_ATTEMPTS)

            # now make more attempts than limit
            register_submission(submission.id, PostSubmissionEvents.on_retry)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            self.assertEqual(submission.registration_attempts, TEST_NUM_ATTEMPTS)

            # added log
            log = TimelineLogProxy.objects.last()
            self.assertEqual(log.event, "registration_attempts_limited")
