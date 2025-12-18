import traceback

import structlog
from celery import group

from openforms.celery import app
from openforms.config.models import GlobalConfiguration
from openforms.logging import logevent
from openforms.submissions.constants import ComponentPreRegistrationStatuses
from openforms.submissions.models import Submission

from .registry import register as formio_registry
from .typing.base import Component

logger = structlog.stdlib.get_logger(__name__)


@app.task
def execute_component_pre_registration(
    submission_id: int, component: Component
) -> None:
    component_key = component["key"]
    submission = Submission.objects.get(id=submission_id)
    log = logger.bind(
        action="formio.component_pre_registration",
        submission_id=submission.uuid,
        component_key=component_key,
        component_type=component["type"],
    )
    log.info("component_pre_registration_task_received")
    logevent.component_pre_registration_start(submission, component_key)

    state = submission.load_submission_value_variables_state()
    component_var = state.get_variable(component_key)

    # if it's already completed
    config = GlobalConfiguration.get_solo()

    if not component_var.is_registration_attempt_allowed:
        log.info(
            "component_pre_registration_skip",
            pre_registration_status=component_var.pre_registration_status,
            registration_attempts=submission.registration_attempts,
            max_number_of_attempts=config.registration_attempt_limit,
        )
        logevent.component_pre_registration_skip(submission, component_key)
        return

    component_var.pre_registration_status = ComponentPreRegistrationStatuses.in_progress
    component_var.save(update_fields=["pre_registration_status"])

    try:
        result = formio_registry.apply_pre_registration_hook(component, submission)
    except Exception as exc:
        log.info("component_pre_registration_failure", exc_info=exc)
        logevent.component_pre_registration_failure(
            submission, error=exc, component_key=component_key
        )
        component_var.pre_registration_status = ComponentPreRegistrationStatuses.failed
        component_var.pre_registration_result = {"traceback": traceback.format_exc()}

        submission.needs_on_completion_retry = True
        submission.save(update_fields=["needs_on_completion_retry"])
    else:
        logevent.component_pre_registration_success(
            submission, component_key=component_key
        )
        component_var.pre_registration_status = ComponentPreRegistrationStatuses.success
        component_var.pre_registration_result = result

    component_var.save(
        update_fields=["pre_registration_status", "pre_registration_result"]
    )


@app.task(bind=True)
def execute_component_pre_registration_group(task, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)

    task_group = group(
        execute_component_pre_registration.si(
            submission_id=submission_id, component=component
        )
        for component in submission.total_configuration_wrapper
        if formio_registry.has_pre_registration_hook(component)
    )

    return task.replace(task_group)
