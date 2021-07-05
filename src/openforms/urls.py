from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.utils.translation import ugettext_lazy as _

from decorator_include import decorator_include

from openforms.emails.admin import EmailTestAdminView

handler500 = "openforms.utils.views.server_error"
admin.site.site_header = "openforms admin"
admin.site.site_title = "openforms admin"
admin.site.index_title = _("Welcome to the Open Forms admin")

urlpatterns = [
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "admin/email/test/",
        admin.site.admin_view(EmailTestAdminView.as_view()),
        name="admin_email_test",
    ),
    path("admin/hijack/", include("hijack.urls")),
    path("admin/", admin.site.urls),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("tinymce/", decorator_include(login_required, "tinymce.urls")),
    path("api/", include("openforms.api.urls", namespace="api")),
    path("auth/", include("openforms.authentication.urls", namespace="authentication")),
    # NOTE: we dont use the User creation feature so don't enable all the mock views
    # path("digid/", include("digid_eherkenning.mock.digid_urls")),
    path("digid/idp/", include("digid_eherkenning.mock.idp.digid_urls")),
    path("", include("openforms.forms.urls", namespace="core")),
    path(
        "privacy-policy",
        include("openforms.privacy_policy.urls", namespace="privacy-policy"),
    ),
]

# NOTE: The staticfiles_urlpatterns also discovers static files (ie. no need to run collectstatic). Both the static
# folder and the media folder are only served via Django if DEBUG = True.
urlpatterns += staticfiles_urlpatterns() + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG and apps.is_installed("debug_toolbar"):
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if apps.is_installed("rosetta"):
    urlpatterns = [path("rosetta/", include("rosetta.urls"))] + urlpatterns
