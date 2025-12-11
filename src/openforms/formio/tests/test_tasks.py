from unittest.mock import patch

from django.test import TestCase, override_settings

from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import BasePlugin, ComponentRegistry
from ..tasks import (
    pre_registration_component_group_task,
    pre_registration_component_task,
)
from ..typing import Component


def do_something(component, submission): ...


class NoHookComponent(Component): ...


class HookComponent(Component): ...


class NoHook(BasePlugin[NoHookComponent]): ...


class Hook(BasePlugin[HookComponent]):
    @staticmethod
    def pre_registration_hook(component: HookComponent, submission: Submission):
        do_something(component, submission)


register = ComponentRegistry()
register("noHook")(NoHook)
register("hook")(Hook)


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

        with patch("openforms.formio.tests.test_tasks.do_something") as mock_func:
            pre_registration_component_task(
                component=hook_component, submission_id=submission.id
            )

            mock_func.assert_called_once_with(hook_component, submission)

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

        with patch("openforms.formio.tests.test_tasks.do_something") as mock_func:
            pre_registration_component_group_task.delay(submission_id=submission.id)

            mock_func.assert_called_once_with(hook_component, submission)
