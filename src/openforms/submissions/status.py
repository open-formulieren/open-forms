"""
Utility to interact with the celery task status.
"""
from dataclasses import dataclass
from typing import Optional

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

    def get_async_result(self) -> Optional[AsyncResult]:
        if not hasattr(self, "_async_result"):
            task_id = self.submission.on_completion_task_id
            self._async_result = AsyncResult(task_id) if task_id else None
        return self._async_result

    @property
    def status(self) -> str:
        result = self.get_async_result()
        is_ready = result.state in states.READY_STATES
        return ProcessingStatuses.done if is_ready else ProcessingStatuses.in_progress

    @property
    def result(self) -> str:
        result = self.get_async_result()
        if result.state == states.SUCCESS:
            return ProcessingResults.success
        if result.state in (states.REVOKED, states.REJECTED):
            return ProcessingResults.retry
        return ProcessingResults.failed

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
        result = self.get_async_result()
        if not result.state == states.SUCCESS:
            return ""
        return self.submission.render_confirmation_page()

    @property
    def report_download_url(self) -> str:
        result = self.get_async_result()
        # only return a download URL if the entire chain succeeded
        if not result.state == states.SUCCESS:
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
        return "TODO"
