from django.urls import path

from .views import EmailVerificationCreateView, TemporaryFileView, VerifyEmailView

app_name = "submissions"

urlpatterns = [
    path(
        "files/<uuid:uuid>",
        TemporaryFileView.as_view(),
        name="temporary-file",
    ),
    path(
        "email-verifications/verify",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path(
        "email-verifications",
        EmailVerificationCreateView.as_view(),
        name="email-verification",
    ),
]
