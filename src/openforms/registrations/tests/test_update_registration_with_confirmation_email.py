from unittest.mock import Mock

from django.test import TestCase

from rest_framework import serializers

from openforms.forms.models import FormRegistrationBackend
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory

from ..base import BasePlugin
from ..registry import Registry
from ..tasks import update_registration_with_confirmation_email
from .utils import patch_registry


class OptionsSerializer(serializers.Serializer):
    string = serializers.CharField()


class UpdateRegistrationWithConfirmationEmailTests(TestCase):
    def test_happy_flow(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            registration_result={"result": "bar"},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            def update_registration_with_confirmation_email(self, submission, options):
                return {"result": "bar"}

        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_result, {"result": "bar"})

        # Check log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(
            log.event, "registration_update_with_confirmation_email_success"
        )

    def test_update_registration_failed(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            registration_result={"result": "bar"},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            def update_registration_with_confirmation_email(self, submission, options):
                raise ValueError("Catastrophic failure")

        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        submission.refresh_from_db()
        self.assertIn(
            "Catastrophic failure",
            submission.registration_result["update_with_confirmation_emails_traceback"],
        )

        # Chack log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(
            log.event, "registration_update_with_confirmation_email_failure"
        )

    def test_main_registration_was_not_completed(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            registration_result={},
            registration_status=RegistrationStatuses.failed,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            update_registration_with_confirmation_email = Mock()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        Plugin.update_registration_with_confirmation_email.assert_not_called()

    def test_no_plugin_is_configured(self):
        submission = SubmissionFactory.create(
            completed=True,
            registration_result={},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        # Chack log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(log.event, "registration_update_with_confirmation_email_skip")

    def test_plugin_was_not_enabled(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"string": "foo"},
            registration_result={},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            @property
            def is_enabled(self):
                return False

            def register_submission(self, submission, options):
                return {}

            update_registration_with_confirmation_email = Mock()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        Plugin.update_registration_with_confirmation_email.assert_not_called()

        # Chack log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(
            log.event, "registration_update_with_confirmation_email_failure"
        )

    def test_options_not_valid(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__registration_backend="plugin",
            form__registration_backend_options={"invalid_option": "foo"},
            registration_result={},
            registration_status=RegistrationStatuses.success,
        )

        register = Registry()

        @register("plugin")
        class Plugin(BasePlugin):
            verbose_name = "Cool plugin"
            configuration_options = OptionsSerializer

            def register_submission(self, submission, options):
                return {}

            update_registration_with_confirmation_email = Mock()

        # Call the hook for the submission, while patching the model field registry
        model_field = FormRegistrationBackend._meta.get_field("backend")
        with patch_registry(model_field, register):
            update_registration_with_confirmation_email(submission.pk)

        Plugin.update_registration_with_confirmation_email.assert_not_called()

        # Chack log
        log = TimelineLogProxy.objects.last()
        self.assertEqual(
            log.event, "registration_update_with_confirmation_email_failure"
        )
