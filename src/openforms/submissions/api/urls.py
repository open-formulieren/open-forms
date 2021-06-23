from django.urls import path

from openforms.submissions.api.views import (
    CheckReportStatusView,
    DownloadSubmissionReportView,
)

app_name = "submission"

urlpatterns = [
    path(
        "<int:report_id>/<str:token>/download",
        DownloadSubmissionReportView.as_view(),
        name="download-submission",
    ),
    path(
        "<int:report_id>/<str:token>/status",
        CheckReportStatusView.as_view(),
        name="submission-report-status",
    ),
]
