from django.urls import path

from .views import (
    DownloadSubmissionReportView,
    SuspendedSubmissionListView,
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
    # TODO do we want this here? it is not a regular UI API? or is it?
    path("suspended", SuspendedSubmissionListView.as_view(), name="suspended"),
]
