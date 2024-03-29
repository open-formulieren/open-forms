from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.urls import include, path

from maykin_2fa import monkeypatch_admin
from maykin_2fa.urls import urlpatterns, webauthn_urlpatterns
from mozilla_django_oidc_db.views import AdminLoginFailure

from openforms.emails.admin import EmailTestAdminView
from openforms.utils.urls import decorator_include

from .views import AdminLoginRedirectView, ClassicAdminLoginView

# Configure admin
monkeypatch_admin()

urlpatterns = [
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "email/test/",
        admin.site.admin_view(EmailTestAdminView.as_view()),
        name="admin_email_test",
    ),
    path("hijack/", include("hijack.urls")),
    path(
        "config/",
        decorator_include(
            staff_member_required, "openforms.config.urls", namespace="config"
        ),
    ),
    path("login/failure/", AdminLoginFailure.as_view(), name="admin-oidc-error"),
    # Custom views on top of maykin-2fa even for OIDC redirect if staff users are not
    # authenticated.
    path("login/", AdminLoginRedirectView.as_view()),  # dispatcher
    path("classic-login/", ClassicAdminLoginView.as_view(), name="admin-mfa-login"),
    # Use custom login views for the admin + support hardware tokens
    path("", include((urlpatterns, "maykin_2fa"))),
    path("", include((webauthn_urlpatterns, "two_factor"))),
    path("", admin.site.urls),
]
