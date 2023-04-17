from django.urls import path

from .views import (
    DownloadSubmissionReportView,
    RetrieveSubmissionForCosignView,
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
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
    path(
        "retrieve-submission-for-cosign",
        RetrieveSubmissionForCosignView.as_view(),
        name="retrieve-submission-for-cosign",
    ),
]
