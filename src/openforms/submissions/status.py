"""
Utility to interact with the celery task status.
"""
from dataclasses import dataclass
from typing import Optional

from django.urls import reverse

from celery import states
from celery.result import AsyncResult
from rest_framework.request import Request

from .models import Submission
from .tokens import token_generator


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
    def state(self) -> str:
        result = self.get_async_result()
        return result.state if result else ""

    @property
    def processing_aborted(self) -> bool:
        return self.state == states.FAILURE  # TODO: verify

    @property
    def error_message(self):
        # TODO: check if there's appointment info
        return ""

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
        token = token_generator.make_token(report)
        download_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )
        return self.request.build_absolute_uri(download_url)

    @property
    def payment_url(self) -> str:
        return "TODO"
