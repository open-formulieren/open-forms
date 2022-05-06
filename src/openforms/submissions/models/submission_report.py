from typing import Optional

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _

from celery.result import AsyncResult
from privates.fields import PrivateMediaFileField

from openforms.utils.pdf import render_to_pdf

from ..report import Report


class SubmissionReport(models.Model):
    title = models.CharField(
        verbose_name=_("title"),
        max_length=200,
        help_text=_("Title of the submission report"),
    )
    content = PrivateMediaFileField(
        verbose_name=_("content"),
        upload_to="submission-reports/%Y/%m/%d",
        help_text=_("Content of the submission report"),
    )
    submission = models.OneToOneField(
        to="Submission",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("submission"),
        help_text=_("Submission the report is about."),
        related_name="report",
    )
    last_accessed = models.DateTimeField(
        verbose_name=_("last accessed"),
        blank=True,
        null=True,
        help_text=_(
            "When the submission report was last accessed. This value is "
            "updated when the report is downloaded."
        ),
    )
    task_id = models.CharField(
        verbose_name=_("task id"),
        max_length=200,
        help_text=_(
            "ID of the celery task creating the content of the report. This is "
            "used to check the generation status."
        ),
        blank=True,
    )

    class Meta:
        verbose_name = _("submission report")
        verbose_name_plural = _("submission reports")

    def __str__(self):
        return self.title

    def generate_submission_report_pdf(self) -> str:
        """
        Generate the submission report as a PDF.

        :return: string with the HTML used for the PDF generation, so that contents
          can be tested.
        """
        form = self.submission.form
        html_report, pdf_report = render_to_pdf(
            "report/submission_report.html",
            context={"report": Report(self.submission)},
        )
        self.content = ContentFile(
            content=pdf_report,
            name=f"{form.name}.pdf",  # Takes care of replacing spaces with underscores
        )
        self.save()
        return html_report

    def get_celery_task(self) -> Optional[AsyncResult]:
        if not self.task_id:
            return

        return AsyncResult(id=self.task_id)
