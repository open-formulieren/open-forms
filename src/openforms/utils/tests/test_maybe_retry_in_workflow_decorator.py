import time
from unittest.mock import patch

from django.test import SimpleTestCase, tag

from celery.exceptions import Retry

from openforms.celery import app

from ..celery import maybe_retry_in_workflow

# Simple tasks


@maybe_retry_in_workflow(timeout=4)
@app.task
def task_within_timeout():
    time.sleep(0.1)
    raise Exception("Retry me")


@maybe_retry_in_workflow(timeout=2)
@app.task
def task_exceeds_timeout():
    time.sleep(1.1)
    raise Exception("Retry me")


# Custom retry logic


class SpecificException(Exception):
    pass


@maybe_retry_in_workflow(timeout=3, retry_for=(SpecificException,))
@app.task
def task_only_retry_for_particular_exception():
    raise Exception("I should not be retried")


def should_retry(exception: SpecificException, task) -> bool:
    return exception.args[0] == "yes"


@maybe_retry_in_workflow(
    timeout=3, retry_for=(SpecificException,), should_retry=should_retry
)
@app.task
def task_only_retry_with_exception_check(text: str):
    raise SpecificException(text)


@tag("slow")
class DecoratorTests(SimpleTestCase):
    def _run_task(self, task: callable, *args, **kwargs):
        # ensure the task request has an ID, so that it *looks* like this was called
        # via celery. This sets the context for the celery request and we need to do
        # some effort to make it look like it's a real celery execution.
        # See :class:`celery.app.task.Context`.
        task.push_request(
            args=args,
            kwargs=kwargs,
            id="some-id",
            task=f"{__name__}.{task.__qualname__}",
            called_directly=False,
        )
        self.addCleanup(task.pop_request)
        task.run(*args, **kwargs)

    def test_task_retried_within_timeout(self):
        with patch.object(
            task_within_timeout, "signature_from_request"
        ) as mock_signature_from_request:
            with self.assertRaises(Retry):
                self._run_task(task_within_timeout)

        # bit of a celery implementation detail, but we mock it to prevent actually
        # sending things to the real redis broker
        mock_signature_from_request.assert_called_once()

    def test_task_retried_outside_timeout(self):
        try:
            with patch.object(
                task_exceeds_timeout, "signature_from_request"
            ) as mock_signature_from_request:
                self._run_task(task_exceeds_timeout)
        except Retry:
            self.fail("Task should have been re-scheduled")
        else:
            mock_signature_from_request.assert_called_once()
            call_kwargs = mock_signature_from_request.call_args.kwargs
            self.assertIn("countdown", call_kwargs)
            self.assertEqual(call_kwargs["retries"], 1)
            mock_signature_from_request.return_value.apply_async.assert_called_once_with()

    def test_conditional_retry_based_on_specific_exception(self):
        try:
            with self.assertRaisesMessage(Exception, "I should not be retried"):
                self._run_task(task_only_retry_for_particular_exception)
        except Retry:
            self.fail("Task should not have been retried")

    def test_conditional_retry_based_on_exception_introspection(self):
        with self.subTest("No retry"):
            message = "no retry"
            try:
                with self.assertRaisesMessage(Exception, message):
                    self._run_task(task_only_retry_with_exception_check, message)
            except Retry:
                self.fail("Task should not have been retried")

        with self.subTest("With retry"):
            with self.assertRaises(Retry):
                self._run_task(task_only_retry_with_exception_check, "yes")
