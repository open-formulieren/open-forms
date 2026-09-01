from unittest.mock import patch

from django.test import TestCase, override_settings

import msgspec

from formio_types import Email, Number, TextField
from openforms.formio.registry import (
    BasePlugin,
    ComponentPreRegistrationResult,
    ComponentRegistry,
)
from openforms.formio.typing import Component
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.constants import ComponentPreRegistrationStatuses
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ..tasks import (
    execute_component_pre_registration,
    execute_component_pre_registration_group,
    process_component_pre_registration,
)

# Wire up a different registry with the real formio types.

register = ComponentRegistry()


@register("textfield")
class NoHook(BasePlugin[TextField]):
    def build_serializer_field(self, component, parent_key_prefix):
        raise NotImplementedError()


@register("email")
class Hook(BasePlugin[Email]):
    def build_serializer_field(self, component, parent_key_prefix):
        raise NotImplementedError()

    @staticmethod
    def pre_registration_hook(
        component: Email, submission: Submission
    ) -> ComponentPreRegistrationResult:
        return {"data": "something"}


@register("number")
class FailHook(BasePlugin[Number]):
    def build_serializer_field(self, component, parent_key_prefix):
        raise NotImplementedError()

    @staticmethod
    def pre_registration_hook(
        component: Number, submission: Submission
    ) -> ComponentPreRegistrationResult:
        raise ValueError("Something went wrong")


class PreRegistrationTaskTests(TestCase):
    def setUp(self):
        super().setUp()

        patcher = patch("openforms.registrations.tasks.formio_registry", register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pre_registration_task(self):
        hook_component: Component = msgspec.to_builtins(
            Email(key="withHook", label="With Hook")
        )
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )

        execute_component_pre_registration(
            component=hook_component, submission_id=submission.pk
        )

        state = submission.variables_state
        component_var = state.variables["withHook"]

        self.assertEqual(
            component_var.pre_registration_status,
            ComponentPreRegistrationStatuses.success,
        )
        self.assertEqual(component_var.pre_registration_result, {"data": "something"})

    def test_pre_registration_task_fail(self):
        failed_hook_component: Component = msgspec.to_builtins(
            Number(key="failedHook", label="Failed Hook")
        )
        submission = SubmissionFactory.from_components(
            [failed_hook_component],
            {"failedHook": 67},
        )

        execute_component_pre_registration(
            component=failed_hook_component, submission_id=submission.pk
        )

        state = submission.variables_state
        component_var = state.variables["failedHook"]

        self.assertEqual(
            component_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", component_var.pre_registration_result)

    def test_preregistration_task_skipped(self):
        hook_component: Component = msgspec.to_builtins(
            Email(key="withHook", label="With Hook")
        )
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )
        state = submission.variables_state
        component_var = state.variables["withHook"]
        component_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        component_var.save()

        execute_component_pre_registration(
            component=hook_component, submission_id=submission.pk
        )

        # Assert that the pre-registration hook isn't run, as the pre-registration status
        # is already set to success
        self.assertIsNone(component_var.pre_registration_result)
        # check logs
        logs = TimelineLogProxy.objects.for_object(submission)
        self.assertEqual(
            logs.filter_event("component_pre_registration_skip").count(), 1
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_pre_registration_group(self):
        no_hook_component = TextField(key="withoutHook", label="Without Hook")
        hook_component = Email(key="withHook", label="With Hook")
        components = msgspec.to_builtins([no_hook_component, hook_component])

        submission = SubmissionFactory.from_components(
            components,
            {"withoutHook": "foo", "withHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)

        state = submission.variables_state
        no_hook_var = state.variables["withoutHook"]
        hook_var = state.variables["withHook"]

        self.assertEqual(
            no_hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.not_used,
        )
        self.assertIsNone(no_hook_var.pre_registration_result)

        self.assertEqual(
            hook_var.pre_registration_status, ComponentPreRegistrationStatuses.success
        )
        self.assertEqual(hook_var.pre_registration_result, {"data": "something"})

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_pre_registration_group_failed(self):
        no_hook_component = TextField(key="withoutHook", label="Without Hook")
        failed_hook_component = Number(key="failedHook", label="Failed Hook")
        components = msgspec.to_builtins([no_hook_component, failed_hook_component])

        submission = SubmissionFactory.from_components(
            components,
            {"withoutHook": "foo", "failedHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)

        state = submission.variables_state
        no_hook_var = state.variables["withoutHook"]
        failed_hook_var = state.variables["failedHook"]

        self.assertEqual(
            no_hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.not_used,
        )
        self.assertIsNone(no_hook_var.pre_registration_result)

        self.assertEqual(
            failed_hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", failed_hook_var.pre_registration_result)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_pre_registration_group_one_component_succeed_and_another_failed(self):
        hook_component = Email(key="withHook", label="With Hook")
        failed_hook_component = Number(key="failedHook", label="Failed Hook")
        components = msgspec.to_builtins([hook_component, failed_hook_component])

        submission = SubmissionFactory.from_components(
            components,
            {"withHook": "foo", "failedHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)

        state = submission.variables_state
        hook_var = state.variables["withHook"]
        failed_hook_var = state.variables["failedHook"]

        self.assertEqual(
            hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.success,
        )
        self.assertEqual(hook_var.pre_registration_result, {"data": "something"})

        self.assertEqual(
            failed_hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", failed_hook_var.pre_registration_result)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_pre_registration_group_component_failed_retried_and_succeed(self):
        hook_component = Email(key="withHook", label="With Hook")
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(hook_component)],
            {"withHook": "foo"},
        )

        # 1st run - fail
        with patch(
            "openforms.registrations.tests.test_component_pre_registration_tasks.Hook.pre_registration_hook"
        ) as mock_hook:
            mock_hook.side_effect = ValueError("something went wrong")
            execute_component_pre_registration_group.delay(submission_id=submission.pk)

        state = submission.variables_state
        hook_var = state.variables["withHook"]

        self.assertEqual(
            hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", hook_var.pre_registration_result)

        # 2nd run - success
        execute_component_pre_registration_group.delay(submission_id=submission.pk)

        hook_var.refresh_from_db()
        self.assertEqual(
            hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.success,
        )
        self.assertEqual(hook_var.pre_registration_result, {"data": "something"})

    def test_process_pre_registration_task_succeed(self):
        hook_component = Email(key="withHook", label="With hook")
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(hook_component)],
            {"withHook": "foo"},
        )
        assert submission.needs_on_completion_retry is False

        state = submission.variables_state
        hook_var = state.variables["withHook"]
        hook_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        hook_var.save()

        process_component_pre_registration(submission_id=submission.pk)

        submission.refresh_from_db()
        self.assertFalse(submission.needs_on_completion_retry)

    def test_process_pre_registration_task_failed(self):
        failed_hook_component = Number(key="failedHook", label="Failed Hook")
        submission = SubmissionFactory.from_components(
            [msgspec.to_builtins(failed_hook_component)],
            {"failedHook": "bar"},
        )

        state = submission.variables_state
        failed_hook_var = state.variables["failedHook"]
        failed_hook_var.pre_registration_status = (
            ComponentPreRegistrationStatuses.failed
        )
        failed_hook_var.save()

        process_component_pre_registration(submission_id=submission.pk)

        submission.refresh_from_db()
        self.assertTrue(submission.needs_on_completion_retry)

    def test_process_pre_registration_task_one_component_succeeded_another_failed(self):
        hook_component = Email(key="withHook", label="With Hook")
        failed_hook_component = Number(key="failedHook", label="Failed Hook")
        components = msgspec.to_builtins([hook_component, failed_hook_component])

        submission = SubmissionFactory.from_components(
            components,
            {"withHook": "foo", "failedHook": "bar"},
        )

        state = submission.variables_state
        hook_var = state.variables["withHook"]
        hook_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        hook_var.save()

        failed_hook_var = state.variables["failedHook"]
        failed_hook_var.pre_registration_status = (
            ComponentPreRegistrationStatuses.failed
        )
        failed_hook_var.save()

        process_component_pre_registration(submission_id=submission.pk)

        submission.refresh_from_db()
        self.assertTrue(submission.needs_on_completion_retry)
