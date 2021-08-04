"""
Test the registration hook on submissions.
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone

from celery.exceptions import Retry
from rest_framework import serializers
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.forms.models import Form
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin
from ..exceptions import RegistrationFailed
from ..registry import Registry
from ..tasks import register_submission, resend_submissions
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
            form__registration_backend="callback",
            form__registration_backend_options={
                "string": "some-option",
                "service": cls.service.id,
            },
        )

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

    def test_plugin_with_custom_result_serializer(self):
        register = Registry()

        result_uuid = uuid.uuid4()

        # register the callback, including the assertions
        @register("callback")
        class Plugin(BasePlugin):
            verbose_name = "Assertion callback"
            configuration_options = OptionsSerializer
            backend_feedback_serializer = ResultSerializer

            def register_submission(self, submission, options):
                return {"external_id": result_uuid}

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
            {"external_id": str(result_uuid)},
        )

    @override_settings(CELERY_MAX_RETRIES=-1)
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
        model_field = Form._meta.get_field("registration_backend")
        with patch_registry(model_field, register):
            register_submission(self.submission.id)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.failed
        )
        tb = self.submission.registration_result["traceback"]
        self.assertIn("Can't divide by zero", tb)

    def test_retrying_registration(self):
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
        model_field = Form._meta.get_field("registration_backend")
        with self.assertRaises(Retry):
            with patch_registry(model_field, register):
                register_submission(self.submission.id)

        self.submission.refresh_from_db()
        self.assertEqual(
            self.submission.registration_status, RegistrationStatuses.in_progress
        )

    def test_retrying_registration_already_in_progress_just_returns(self):
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
        model_field = Form._meta.get_field("registration_backend")

        submission = SubmissionFactory.create(
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

    def test_submission_marked_complete_when_form_has_no_registration_backend(self):
        submission_no_registration_backend = SubmissionFactory.create(
            form__registration_backend="", form__registration_backend_options={}
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


class ResendSubmissionTest(TestCase):
    @patch("openforms.registrations.tasks.register_submission.delay")
    def test_resend_submission_task_only_resends_certain_submissions(self, task_mock):
        failed_within_time_limit = SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed, completed_on=timezone.now()
        )
        # Outside time limit
        SubmissionFactory.create(
            registration_status=RegistrationStatuses.failed,
            completed_on=(
                timezone.now()
                - timedelta(
                    hours=settings.CELERY_BEAT_RESEND_SUBMISSIONS_TIME_LIMIT + 1
                )
            ),
        )
        # Not failed
        SubmissionFactory.create(
            registration_status=RegistrationStatuses.pending,
            completed_on=timezone.now(),
        )

        resend_submissions()

        self.assertEqual(task_mock.call_count, 1)
        task_mock.assert_called_once_with(failed_within_time_limit.id)
