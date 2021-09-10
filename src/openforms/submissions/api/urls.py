from django.urls import path

from .views import (
    DownloadSubmissionReportView,
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
        "files/upload",
        TemporaryFileUploadView.as_view(),
        name="temporary-file-upload",
    ),
    path(
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
]
