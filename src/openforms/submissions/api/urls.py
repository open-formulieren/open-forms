from django.urls import path

from .views import EmailVerificationCreateView, TemporaryFileView

app_name = "submissions"

urlpatterns = [
    path(
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
    path(
        "email-verifications",
        EmailVerificationCreateView.as_view(),
        name="email-verification",
    ),
]
