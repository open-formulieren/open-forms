from django.urls import path

from openforms.submissions.api.views import (
    CheckReportStatusView,
    DownloadSubmissionReportView,
    RemovalMethodsView,
    TemporaryFileUploadView,
    TemporaryFileView,
)

app_name = "submissions"

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
    path(
        "files/upload",
        TemporaryFileUploadView.as_view(),
        name="temporary-file-upload",
    ),
    path(
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
    path("removal-methods", RemovalMethodsView.as_view(), name="removal-methods"),
]
