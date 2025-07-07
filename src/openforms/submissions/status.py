"""
Utility to interact with the celery task status.
"""

from dataclasses import dataclass

from django.urls import reverse

from celery import states
from celery.result import AsyncResult
from rest_framework.request import Request

from openforms.appointments.models import AppointmentInfo

from .constants import ProcessingResults, ProcessingStatuses
from .models import Submission
from .utils import add_submmission_to_session, get_report_download_url


@dataclass
class SubmissionProcessingStatus:
    request: Request
    submission: Submission

    def get_async_results(self) -> list[AsyncResult]:
        """Retrieve the results for the task scheduled ONLY when the submission was completed."""
        if not hasattr(self, "_async_result"):
            task_ids = self.submission.post_completion_task_ids
            self._async_results = [AsyncResult(task_id) for task_id in task_ids]
        return self._async_results

    def get_all_async_results(self) -> list[AsyncResult]:
        """Retrieve the results for ALL tasks scheduled while processing a submission.

        This includes tasks scheduled when the submission was completed, when it was cosigned, when a payment was
        received or when a retry flow was triggered.
        """
        if not hasattr(self, "_all_async_results"):
            task_ids_per_event = (
                self.submission.postcompletionmetadata_set.all().values_list(
                    "tasks_ids", flat=True
                )
            )
            task_ids = []
            for tasks_ids_list in task_ids_per_event:
                task_ids += tasks_ids_list

            self._all_async_results = [AsyncResult(task_id) for task_id in task_ids]
        return self._all_async_results

    @property
    def status(self) -> str:
        results = self.get_async_results()
        any_failed = any(result.state == states.FAILURE for result in results)
        all_ready = all(result.state in states.READY_STATES for result in results)
        if results and (any_failed or all_ready):
            return ProcessingStatuses.done
        return ProcessingStatuses.in_progress

    @property
    def result(self) -> str:
        if self.status != ProcessingStatuses.done:
            return ""

        results = self.get_async_results()
        all_success = all(result.state == states.SUCCESS for result in results)
        any_failed = any(result.state == states.FAILURE for result in results)

        if all_success:
            return ProcessingResults.success
        if any_failed:
            return ProcessingResults.failed

        raise RuntimeError(
            "Unexpected result state! Some tasks were not a success (?) but "
            "none failed either. Note that this can mean a task was incorrectly "
            "defined as `ignore_result=True` which prevents us from tracking the state."
        )

    @property
    def error_message(self) -> str:
        # check if we have error information from appointments
        error_bits = []

        # check appointment info - optional one-to-one field
        appointment_info = AppointmentInfo.objects.filter(
            submission=self.submission
        ).first()
        if appointment_info is not None and (
            appointment_error := appointment_info.error_information
        ):
            error_bits.append(appointment_error)
        return "\n\n".join(error_bits)

    @property
    def confirmation_page_title(self) -> str:
        if self.result != ProcessingResults.success:
            return ""
        return self.submission.render_confirmation_page_title()

    @property
    def confirmation_page_content(self) -> str:
        if self.result != ProcessingResults.success:
            return ""
        return self.submission.render_confirmation_page()

    @property
    def report_download_url(self) -> str:
        # only return a download URL if the entire chain succeeded
        if self.result != ProcessingResults.success:
            return ""
        return get_report_download_url(self.request, self.submission.report)

    @property
    def payment_url(self) -> str:
        # don't bother with payment if processing did not succeed.
        if self.result != ProcessingResults.success:
            return ""

        if not self.submission.payment_required:
            return ""

        if self.submission.payment_user_has_paid:
            return ""

        payment_start_url = reverse(
            "payments:start",
            kwargs={
                "uuid": self.submission.uuid,
                "plugin_id": self.submission.form.payment_backend,
            },
        )
        return self.request.build_absolute_uri(payment_start_url)

    def forget_results(self) -> None:
        """
        Clean up the results in the Celery result backend.

        Forgetting the results ensures that we don't leak resources.
        """
        results = self.get_all_async_results()
        for result in results:
            result.forget()

    def ensure_failure_can_be_managed(self) -> None:
        """
        Execute the necessary side-effects to failure can be dealt with.

        Only take these "corrective" measures if the processig is completed and the
        result is "failure".

        This includes:

        * adding the submission ID back to the session after it got removed by completing
          the submission
        """
        if self.result != ProcessingResults.failed:
            return

        # add the submission ID back to the session so details can be retrieved and
        # submission can be completed again after correcting the mistakes.
        add_submmission_to_session(self.submission, self.request.session)
