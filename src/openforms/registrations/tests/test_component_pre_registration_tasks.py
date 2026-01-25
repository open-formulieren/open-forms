from typing import Any
from unittest.mock import patch

from django.test import TestCase, override_settings

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


class NoHookComponent(Component): ...


class HookComponent(Component): ...


class FailHookComponent(Component): ...


class NoHook(BasePlugin[NoHookComponent, Any]): ...


class Hook(BasePlugin[HookComponent, Any]):
    @staticmethod
    def pre_registration_hook(
        component: HookComponent, submission: Submission
    ) -> ComponentPreRegistrationResult:
        return {"data": "something"}


class FailHook(BasePlugin[FailHookComponent, Any]):
    @staticmethod
    def pre_registration_hook(
        component: HookComponent, submission: Submission
    ) -> ComponentPreRegistrationResult:
        raise ValueError("Something went wrong")


register = ComponentRegistry()
register("noHook")(NoHook)
register("hook")(Hook)
register("failHook")(FailHook)


class PreRegistrationTaskTests(TestCase):
    def setUp(self):
        super().setUp()

        patcher = patch("openforms.registrations.tasks.formio_registry", register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_pre_registration_task(self):
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )

        execute_component_pre_registration(
            component=hook_component, submission_id=submission.pk
        )

        state = submission.load_submission_value_variables_state()
        component_var = state.variables["withHook"]

        self.assertEqual(
            component_var.pre_registration_status,
            ComponentPreRegistrationStatuses.success,
        )
        self.assertEqual(component_var.pre_registration_result, {"data": "something"})

    def test_pre_registration_task_fail(self):
        failed_hook_component: Component = {
            "key": "failedHook",
            "type": "failHook",
            "label": "Failed Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [failed_hook_component],
            {"failedHook": "foo"},
        )

        execute_component_pre_registration(
            component=failed_hook_component, submission_id=submission.pk
        )

        state = submission.load_submission_value_variables_state()
        component_var = state.variables["failedHook"]

        self.assertEqual(
            component_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", component_var.pre_registration_result)

    def test_reregistration_task_skipped(self):
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )
        state = submission.load_submission_value_variables_state()
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
        no_hook_component: Component = {
            "key": "withoutHook",
            "type": "nohook",
            "label": "Without Hook",
            "validate": {"required": False},
        }
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [no_hook_component, hook_component],
            {"withoutHook": "foo", "withHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)  # pyright: ignore[reportFunctionMemberAccess]

        state = submission.load_submission_value_variables_state()
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
        no_hook_component: Component = {
            "key": "withoutHook",
            "type": "nohook",
            "label": "Without Hook",
            "validate": {"required": False},
        }
        failed_hook_component: Component = {
            "key": "failedHook",
            "type": "failHook",
            "label": "Failed Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [no_hook_component, failed_hook_component],
            {"withoutHook": "foo", "failedHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)  # pyright: ignore[reportFunctionMemberAccess]

        state = submission.load_submission_value_variables_state()
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
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        failed_hook_component: Component = {
            "key": "failedHook",
            "type": "failHook",
            "label": "Failed Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component, failed_hook_component],
            {"withHook": "foo", "failedHook": "bar"},
        )

        execute_component_pre_registration_group.delay(submission_id=submission.pk)  # pyright: ignore[reportFunctionMemberAccess]

        state = submission.load_submission_value_variables_state()
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
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )

        # 1st run - fail
        with patch(
            "openforms.registrations.tests.test_component_pre_registration_tasks.Hook.pre_registration_hook"
        ) as mock_hook:
            mock_hook.side_effect = ValueError("something went wrong")
            execute_component_pre_registration_group.delay(submission_id=submission.pk)  # pyright: ignore[reportFunctionMemberAccess]

        state = submission.load_submission_value_variables_state()
        hook_var = state.variables["withHook"]

        self.assertEqual(
            hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", hook_var.pre_registration_result)

        # 2nd run - success
        execute_component_pre_registration_group.delay(submission_id=submission.pk)  # pyright: ignore[reportFunctionMemberAccess]

        hook_var.refresh_from_db()
        self.assertEqual(
            hook_var.pre_registration_status,
            ComponentPreRegistrationStatuses.success,
        )
        self.assertEqual(hook_var.pre_registration_result, {"data": "something"})

    def test_process_pre_registration_task_succeed(self):
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component],
            {"withHook": "foo"},
        )
        assert submission.needs_on_completion_retry is False

        state = submission.load_submission_value_variables_state()
        hook_var = state.variables["withHook"]
        hook_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        hook_var.save()

        process_component_pre_registration(submission_id=submission.pk)

        submission.refresh_from_db()
        self.assertFalse(submission.needs_on_completion_retry)

    def test_process_pre_registration_task_failed(self):
        failed_hook_component: Component = {
            "key": "failedHook",
            "type": "failHook",
            "label": "Failed Hook",
            "validate": {"required": False},
        }

        submission = SubmissionFactory.from_components(
            [failed_hook_component],
            {"failedHook": "bar"},
        )

        state = submission.load_submission_value_variables_state()
        failed_hook_var = state.variables["failedHook"]
        failed_hook_var.pre_registration_status = (
            ComponentPreRegistrationStatuses.failed
        )
        failed_hook_var.save()

        process_component_pre_registration(submission_id=submission.pk)

        submission.refresh_from_db()
        self.assertTrue(submission.needs_on_completion_retry)

    def test_process_pre_registration_task_one_component_succeeded_another_failed(self):
        hook_component: Component = {
            "key": "withHook",
            "type": "hook",
            "label": "With Hook",
            "validate": {"required": False},
        }
        failed_hook_component: Component = {
            "key": "failedHook",
            "type": "failHook",
            "label": "Failed Hook",
            "validate": {"required": False},
        }
        submission = SubmissionFactory.from_components(
            [hook_component, failed_hook_component],
            {"withHook": "foo", "failedHook": "bar"},
        )

        state = submission.load_submission_value_variables_state()
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
