"""
Test the registration hook on submissions.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time
from rest_framework import serializers
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.config.models import GlobalConfiguration
from openforms.forms.models import Form
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory

from ...logging.models import TimelineLogProxy
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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            register_submission(self.submission.id)

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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register), self.assertLogs(
            level="WARNING"
        ) as log:
            register_submission(self.submission.id)

            # check we log an WARNING without stack
            error_log = log.records[-1]
            self.assertEqual(error_log.levelname, "WARNING")
            self.assertIn("failed", error_log.message)
            self.assertIsNone(error_log.exc_info)

        self.submission.refresh_from_db()
        self.assertTrue(self.submission.needs_on_completion_retry)
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Can't divide by zero", tb)
        self.assertEqual(self.submission.last_register_date, timezone.now())

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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register), self.assertLogs(
            level="ERROR"
        ) as log:
            register_submission(self.submission.id)

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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")

        last_register_date = timezone.now() - timedelta(hours=1)
        submission = SubmissionFactory.create(
            last_register_date=last_register_date,
            registration_status=RegistrationStatuses.success,
            form__registration_backend="callback",
            form__registration_backend_options={
                "string": "some-option",
                "service": self.service.id,
            },
        )

        with patch_registry(model_field, register):
            # Assert task just returns
            self.assertIsNone(register_submission(submission.id))

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
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, Registry()):
            register_submission(submission_no_registration_backend.id)

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

        with self.assertRaises(RegistrationFailed):
            register_submission(submission.id)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        mock_get_solo.return_value = GlobalConfiguration(
            plugin_configuration={"registrations": {"callback": {"enabled": False}}}
        )

        # # call the hook for the submission, while patching the model field registry
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            with self.assertRaises(RegistrationFailed):
                register_submission(self.submission.id)

        self.submission.refresh_from_db()
        self.assertTrue(self.submission.needs_on_completion_retry)
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Registration plugin is not enabled", tb)
        self.assertEqual(self.submission.last_register_date, timezone.now())


class NumRegistrationsTest(TestCase):
    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
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

            def get_reference_from_result(self, result: dict) -> None:
                pass

        mock_get_solo.return_value = GlobalConfiguration(
            registration_attempt_limit=TEST_NUM_ATTEMPTS,
            plugin_configuration={"registrations": {"callback": {"enabled": True}}},
        )

        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            # first registration won't re-raise RegistrationFailed
            register_submission(submission.id)

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
                    register_submission(submission.id)

                submission.refresh_from_db()
                self.assertEqual(
                    submission.registration_status, RegistrationStatuses.failed
                )
                self.assertEqual(submission.registration_attempts, i)
                # marked for retry
                self.assertTrue(submission.needs_on_completion_retry)

            # check
            self.assertEqual(submission.registration_attempts, TEST_NUM_ATTEMPTS)

            # now make more attempts then limit
            register_submission(submission.id)

            submission.refresh_from_db()
            self.assertEqual(
                submission.registration_status, RegistrationStatuses.failed
            )
            self.assertEqual(submission.registration_attempts, TEST_NUM_ATTEMPTS)
            # no more retries
            self.assertFalse(submission.needs_on_completion_retry)

            # added log
            log = TimelineLogProxy.objects.last()
            self.assertEqual(log.event, "registration_attempts_limited")
