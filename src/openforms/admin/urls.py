from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.urls import include, path

from decorator_include import decorator_include
from mozilla_django_oidc_db.views import AdminLoginFailure

from openforms.emails.admin import EmailTestAdminView

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
    path("", admin.site.urls),
]
