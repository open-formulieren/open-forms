import traceback

import structlog
from celery import group

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import ComponentPreRegistrationStatuses
from openforms.submissions.models import Submission

from .registry import register as formio_registry
from .typing.base import Component

logger = structlog.stdlib.get_logger(__name__)


@app.task
def pre_registration_component_task(component: Component, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    state = submission.load_submission_value_variables_state()
    component_var = state.variables[component["key"]]

    # if it's already completed
    config = GlobalConfiguration.get_solo()

    should_skip = (
        component_var.pre_registration_status
        == ComponentPreRegistrationStatuses.success
        or submission.registration_attempts >= config.registration_attempt_limit
    )
    if should_skip:
        logger.info(
            "component_pre_registration_hook_skip",
            component=component["key"],
            pre_registration_status=component_var.pre_registration_status,
            registration_attempts=submission.registration_attempts,
            max_number_of_attempts=config.registration_attempt_limit,
        )
        return

    component_var.pre_registration_status = ComponentPreRegistrationStatuses.in_progress
    component_var.save(update_fields=["pre_registration_status"])

    try:
        result = formio_registry.apply_pre_registration_hook(component, submission)
    except Exception as exc:
        logger.info("component_pre_registration_hook_failure", exc_info=exc)
        component_var.pre_registration_status = ComponentPreRegistrationStatuses.failed
        component_var.pre_registration_result = {"traceback": traceback.format_exc()}

        submission.needs_on_completion_retry = True
        submission.save(
            update_fields=[
                "needs_on_completion_retry"
            ]  # todo move after the group task
        )
    else:
        component_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        component_var.pre_registration_result = result

    component_var.save(
        update_fields=["pre_registration_status", "pre_registration_result"]
    )


@app.task(bind=True)
def pre_registration_component_group_task(task, submission_id: int) -> None:
    # todo replace with chord?
    submission = Submission.objects.get(id=submission_id)

    task_group = group(
        pre_registration_component_task.si(component, submission_id)
        for component in submission.total_configuration_wrapper
        if formio_registry.has_pre_registration_hook(component)
    )

    return task.replace(task_group)
