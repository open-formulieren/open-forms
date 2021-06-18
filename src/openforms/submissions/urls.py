from django.urls import path

from openforms.submissions.views import DownloadSubmissionReportView

app_name = "submission"

urlpatterns = [
    path(
        "<int:report_id>/<str:token>/download",
        DownloadSubmissionReportView.as_view(),
        name="download-submission",
    ),
]
