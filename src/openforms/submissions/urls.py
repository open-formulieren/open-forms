from django.urls import path

from .views import ResumeSubmissionView, SubmissionAttachmentDownloadView

app_name = "submissions"

urlpatterns = [
    path(
        "<uuid:submission_uuid>/<str:token>/resume",
        ResumeSubmissionView.as_view(),
        name="resume",
    ),
    path(
        "attachment/<uuid:uuid>/download/",
        SubmissionAttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
]
