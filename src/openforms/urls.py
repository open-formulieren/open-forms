from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from decorator_include import decorator_include

from openforms.accounts.oidc.views import AdminLoginFailure
from openforms.emails.admin import EmailTestAdminView
from openforms.emails.views import EmailWrapperTestView
from openforms.submissions.dev_views import SubmissionPDFTestView
from openforms.utils.views import ErrorDetailView

handler500 = "openforms.utils.views.server_error"
admin.site.site_header = "openforms admin"
admin.site.site_title = "openforms admin"
admin.site.index_title = _("Welcome to the Open Forms admin")
admin.site.enable_nav_sidebar = False

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
    path(
        "admin/config/",
        decorator_include(
            staff_member_required, "openforms.config.urls", namespace="config"
        ),
    ),
    path("admin/login/failure/", AdminLoginFailure.as_view(), name="admin-oidc-error"),
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
    path("cookies/", include("cookie_consent.urls")),
    path("tinymce/", decorator_include(login_required, "tinymce.urls")),
    path("api/", include("openforms.api.urls", namespace="api")),
    path("auth/", include("openforms.authentication.urls", namespace="authentication")),
    path(
        "appointments/",
        include("openforms.appointments.urls", namespace="appointments"),
    ),
    path("csp/", include("cspreports.urls")),
    path(
        "submissions/",
        include("openforms.submissions.urls", namespace="submissions"),
    ),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path(
        "digid-oidc/",
        include(
            "openforms.authentication.contrib.digid_eherkenning_oidc.digid_urls",
            namespace="digid_oidc",
        ),
    ),
    path(
        "eherkenning-oidc/",
        include(
            "openforms.authentication.contrib.digid_eherkenning_oidc.eherkenning_urls",
            namespace="eherkenning_oidc",
        ),
    ),
    path("payment/", include("openforms.payments.urls", namespace="payments")),
    # NOTE: we dont use the User creation feature so don't enable all the mock views
    path("digid/", include("openforms.authentication.contrib.digid.urls")),
    path("eherkenning/", include("openforms.authentication.contrib.eherkenning.urls")),
    path("digid/idp/", include("digid_eherkenning.mock.idp.digid_urls")),
    path("fouten/<exception_class>/", ErrorDetailView.as_view(), name="error-detail"),
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

if settings.DEBUG:
    from openforms.forms.models import Form

    urlpatterns += [
        path(
            "dev/email/wrapper",
            EmailWrapperTestView.as_view(),
            name="dev-email-wrapper",
        ),
        path(
            "dev/email/confirmation/<int:submission_id>",
            EmailWrapperTestView.as_view(),
            name="dev-email-confirm",
        ),
        path(
            "dev/submissions/<int:pk>/pdf",
            SubmissionPDFTestView.as_view(),
            name="dev-submissions-pdf",
        ),
        path(
            "dev/react",
            TemplateView.as_view(
                template_name="debug.html",
                extra_context={"opts": Form._meta},
            ),
        ),
    ]

if apps.is_installed("rosetta"):
    urlpatterns = [path("admin/rosetta/", include("rosetta.urls"))] + urlpatterns

if apps.is_installed("silk"):
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

# render a form detail page, as catch-all since it takes the slug of a form
urlpatterns += [
    path("", include("openforms.forms.urls", namespace="core")),
]
