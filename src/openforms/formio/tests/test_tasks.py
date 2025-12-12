from unittest.mock import patch

from django.test import TestCase, override_settings

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ...submissions.constants import ComponentPreRegistrationStatuses
from ..registry import BasePlugin, ComponentRegistry
from ..tasks import (
    pre_registration_component_group_task,
    pre_registration_component_task,
)
from ..typing import Component
from ..typing.base import ComponentPreRegistrationResult


class NoHookComponent(Component): ...


class HookComponent(Component): ...


class FailHookComponent(Component): ...


class NoHook(BasePlugin[NoHookComponent]): ...


class Hook(BasePlugin[HookComponent]):
    @staticmethod
    def pre_registration_hook(
        component: HookComponent, submission: Submission
    ) -> ComponentPreRegistrationResult:
        return {"data": "something"}


class FailHook(BasePlugin[FailHookComponent]):
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

        patcher = patch("openforms.formio.tasks.formio_registry", register)
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

        pre_registration_component_task(
            component=hook_component, submission_id=submission.id
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
        assert submission.needs_on_completion_retry is False

        pre_registration_component_task(
            component=failed_hook_component, submission_id=submission.id
        )

        state = submission.load_submission_value_variables_state()
        component_var = state.variables["failedHook"]

        self.assertEqual(
            component_var.pre_registration_status,
            ComponentPreRegistrationStatuses.failed,
        )
        self.assertIn("traceback", component_var.pre_registration_result)

        submission.refresh_from_db()
        self.assertTrue(submission.needs_on_completion_retry)

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

        pre_registration_component_task(
            component=hook_component, submission_id=submission.id
        )

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

        pre_registration_component_group_task.delay(submission_id=submission.id)

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
        assert submission.needs_on_completion_retry is False

        pre_registration_component_group_task.delay(submission_id=submission.id)

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

        submission.refresh_from_db()
        self.assertTrue(submission.needs_on_completion_retry)
