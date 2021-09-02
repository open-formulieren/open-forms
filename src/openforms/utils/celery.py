import logging
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Union

from celery.app.task import Task
from celery.utils.time import get_exponential_backoff_interval

logger = logging.getLogger(__name__)

ExceptionCls = type(Exception)


def default_should_retry(exception: Exception, task: Task) -> bool:
    return True


def maybe_retry_in_workflow(
    timeout: Union[float, int] = 10,  # in seconds
    retry_backoff: bool = True,  # exponential backoff
    should_retry: Optional[Callable[[Exception, Task], bool]] = None,
    retry_for: Tuple[ExceptionCls] = (Exception,),
):
    """
    Decorate a celery task with conditional retry-behaviour.

    Normally, when a celery task is part of a workflow (such as in a chain) and the
    task can be retried, the retries will all be attempted before the next task
    is executed. This decorator adds a timeout check to limit the maximum time
    that can be spent in retries inside the workflow. If the next retry attempt would
    exceed this timeout, the task is re-scheduled outside of the workflow.

    This works by passing headers which are available on the task request context - we
    can track the total actual execution time and compare that to the configured
    timeout.
    """
    should_retry = should_retry or default_should_retry()

    def decorator(task):
        @wraps(task.run)
        def run(*args, **kwargs):
            has_timeout = getattr(task.request, "has_timeout", True)
            logger.debug(
                "Task %s (%s) timeout relevant: %s",
                task.request.id,
                task.request.task,
                has_timeout,
            )

            retries: int = task.request.retries
            total_runtime = (
                0 if retries == 0 else getattr(task.request, "total_runtime", 0)
            )

            do_retry, err = False, None
            start = time.time()
            try:
                return task._orig_run(*args, **kwargs)
            except retry_for as exc:
                if not should_retry(exc, task):
                    raise
                do_retry, err = True, exc
            finally:
                end = time.time()

            # an exception of some kind happened and we *may* have to retry
            if not do_retry:
                logger.debug("No retry is needed, existing.")
                return

            total_runtime += end - start
            logger.debug("Total accumulated runtime: %f", total_runtime)

            countdown = get_exponential_backoff_interval(
                factor=1,
                retries=retries,
                maximum=timeout
                if has_timeout
                else getattr(task, "retry_backoff_max", 600),
                full_jitter=False,  # no jitter
            )
            logger.debug("Planned retry countdown: %ds", countdown)
            # add the planned countdown to the runtime, as this spans the retry attempts
            total_runtime += countdown

            # now we enter the check whether to retry IN the workflow, or if it would
            # exceed the timeout, meaning we schedule it OUTSIDE the workflow.
            if has_timeout and total_runtime >= timeout:
                logger.debug("Scheduling retries OUTSIDE of the current workflow")
                signature = task.signature_from_request(
                    task.request,
                    args=None,
                    kwargs=None,
                    countdown=countdown,
                    eta=None,
                    retries=retries + 1,
                    headers={"has_timeout": False},
                )
                signature.apply_async()
                return
            else:
                logger.debug("Scheduling retry inside of current workflow")
                raise task.retry(
                    exc=err,
                    countdown=countdown,
                    # pass metadata that can be accessed from the task.request context again
                    headers={
                        "total_runtime": total_runtime,
                        "has_timeout": has_timeout,
                    },
                )

        task._orig_run, task.run = task.run, run

        return task

    return decorator
