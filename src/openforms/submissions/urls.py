from django.urls import path

from .views import ResumeSubmissionView

app_name = "submissions"

urlpatterns = [
    path(
        "<uuid:submission_uuid>/<str:token>/resume",
        ResumeSubmissionView.as_view(),
        name="resume",
    )
]
