
import structlog
from celery import group

from openforms.celery import app
from openforms.submissions.models import Submission

from .registry import register as formio_registry
from .typing.base import Component

logger = structlog.stdlib.get_logger(__name__)


@app.task
def pre_registration_component_task(component: Component, submission_id: int) -> None:
    submission = Submission.objects.get(id=submission_id)
    formio_registry.apply_pre_registration_hook(component, submission)


@app.task(bind=True)
def pre_registration_component_group_task(task, submission_id: int) -> None:
    # todo replace with chord?
    submission = Submission.objects.get(id=submission_id)

    task_group = group(
        pre_registration_component_task.si(component, submission_id)
        for component in submission.total_configuration_wrapper
        #     todo if some property?
    )

    return task.replace(task_group=task_group)
