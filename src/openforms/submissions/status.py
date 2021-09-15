"""
Utility to interact with the celery task status.
"""
from dataclasses import dataclass
from typing import List

from django.urls import reverse

from celery import states
from celery.result import AsyncResult
from rest_framework.request import Request

from openforms.appointments.models import AppointmentInfo

from .constants import ProcessingResults, ProcessingStatuses
from .models import Submission
from .tokens import submission_report_token_generator


@dataclass
class SubmissionProcessingStatus:
    request: Request
    submission: Submission

    def get_async_results(self) -> List[AsyncResult]:
        if not hasattr(self, "_async_result"):
            task_ids = self.submission.on_completion_task_ids
            self._async_results = [AsyncResult(task_id) for task_id in task_ids]
        return self._async_results

    @property
    def status(self) -> str:
        results = self.get_async_results()
        any_failed = any((result.state == states.FAILURE for result in results))
        all_ready = all((result.state in states.READY_STATES for result in results))
        if results and (any_failed or all_ready):
            return ProcessingStatuses.done
        return ProcessingStatuses.in_progress

    @property
    def result(self) -> str:
        if self.status != ProcessingStatuses.done:
            return ""

        results = self.get_async_results()
        all_success = all((result.state == states.SUCCESS for result in results))
        any_failed = any((result.state == states.FAILURE for result in results))

        if all_success:
            return ProcessingResults.success
        if any_failed:
            return ProcessingResults.failed

        # TODO: not sure if we can actually get to this? Maybe this should be removed.
        return ProcessingResults.retry

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
    def confirmation_page_content(self) -> str:
        if self.result != ProcessingResults.success:
            return ""
        return self.submission.render_confirmation_page()

    @property
    def report_download_url(self) -> str:
        # only return a download URL if the entire chain succeeded
        if self.result != ProcessingResults.success:
            return ""
        report = self.submission.report
        token = submission_report_token_generator.make_token(report)
        download_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )
        return self.request.build_absolute_uri(download_url)

    @property
    def payment_url(self) -> str:
        # don't bother with payment if processing did not succeed.
        if self.result != ProcessingResults.success:
            return ""

        if not self.submission.payment_required:
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
        results = self.get_async_results()
        for result in results:
            result.forget()
