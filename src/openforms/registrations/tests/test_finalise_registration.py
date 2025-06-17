from unittest.mock import Mock

from django.test import TestCase

from rest_framework import serializers

from openforms.forms.models import FormRegistrationBackend
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin
from ..exceptions import RegistrationFailed
from ..registry import Registry
from ..tasks import finalise_registration
from .utils import patch_registry


class OptionsSerializer(serializers.Serializer):
    string = serializers.CharField()


class FinaliseRegistrationTests(TestCase):
    def test_happy_flow(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            main_registration_completed=True,
            registration_result={},
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            def finalise_register_submission(self, submission, options):
                return {"result": "bar"}

        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            finalise_registration(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)
        self.assertEqual(submission.registration_result, {"result": "bar"})

        # Check log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(log.event, "registration_success")

    def test_finalise_registration_failed(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            main_registration_completed=True,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            def finalise_register_submission(self, submission, options):
                raise ValueError("Catastrophic failure")

        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            with self.subTest("On completion"):
                try:
                    finalise_registration(
                        submission.id, PostSubmissionEvents.on_completion
                    )
                except RegistrationFailed as exc:
                    raise self.failureException("Should not raise") from exc

            with self.subTest("On retry"), self.assertRaises(ValueError):
                finalise_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
        self.assertIn(
            "Catastrophic failure", submission.registration_result["traceback"]
        )

        # Check log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(log.event, "registration_failure")

    def test_main_registration_was_not_completed(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            main_registration_completed=False,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            finalise_register_submission = Mock()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            finalise_registration(submission.id, PostSubmissionEvents.on_completion)

        Plugin.finalise_register_submission.assert_not_called()

    def test_does_not_execute_on_retry_when_already_successful(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            finalise_register_submission = Mock()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            finalise_registration(submission.id, PostSubmissionEvents.on_retry)

        Plugin.finalise_register_submission.assert_not_called()

    def test_remove_traceback_when_finalise_registration_was_successful(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            main_registration_completed=True,
            registration_status=RegistrationStatuses.failed,
            registration_result={"traceback": "Catastrophic failure"},
            registration_attempts=1,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            def finalise_register_submission(self, submission, options):
                return {"result": "bar"}

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            finalise_registration(submission.id, PostSubmissionEvents.on_retry)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)
        self.assertNotIn("traceback", submission.registration_result)

    def test_maximum_registration_attempts_exceeded(self):
        pass

    def test_no_plugin_is_configured(self):
        pass

    def test_plugin_was_not_enabled(self):
        pass

    def test_options_not_valid(self):
        pass
