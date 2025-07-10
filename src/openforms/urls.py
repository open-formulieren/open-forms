from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from openforms.emails.views import EmailWrapperTestView
from openforms.submissions.dev_views import SubmissionPDFTestView
from openforms.utils.urls import decorator_include
from openforms.utils.views import ErrorDetailView, SDKRedirectView

handler500 = "maykin_common.views.server_error"
admin.site.site_header = "openforms admin"
admin.site.site_title = "openforms admin"
admin.site.index_title = _("Welcome to the Open Forms admin")
admin.site.enable_nav_sidebar = False

# DeprecationWarning
# TODO: remove in Open Forms 3.0 - these are moved to /auth/oidc/*
_legacy_oidc_urls = [
    path(
        "",
        include("openforms.authentication.contrib.digid_eherkenning_oidc.legacy_urls"),
    ),
    path(
        "org-oidc/",
        include("openforms.authentication.contrib.org_oidc.urls"),
    ),
    # still included so that URL reversing for the authentication request view works
    path("oidc/", include("mozilla_django_oidc.urls")),  # moved to /auth/oidc
    # included with namespace for backwards compatibility reasons
    path(
        "oidc/",
        include(([path("", include("mozilla_django_oidc.urls"))], "legacy_oidc")),
    ),
]

urlpatterns = [
    path("admin/", include("openforms.admin.urls")),
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
    path("tinymce/", decorator_include(login_required, "tinymce.urls")),  # type: ignore
    path("api/", include("openforms.api.urls", namespace="api")),
    *_legacy_oidc_urls,
    path("auth/oidc/", include("mozilla_django_oidc.urls")),
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
    path("payment/", include("openforms.payments.urls", namespace="payments")),
    # NOTE: we dont use the User creation feature so don't enable all the mock views
    path("digid/", include("openforms.authentication.contrib.digid.urls")),
    path("eherkenning/", include("openforms.authentication.contrib.eherkenning.urls")),
    path("digid/idp/", include("digid_eherkenning.mock.idp.digid_urls")),
    path("fouten/<exception_class>/", ErrorDetailView.as_view(), name="error-detail"),
    # we can't expose the digid/eherkenning metadata under .well-known as it requires
    # registration (see RFC5785)
    path("discovery/digid-eherkenning/", include("digid_eherkenning.metadata_urls")),
    # stable SDK urls
    path(
        f"{settings.STATIC_URL.lstrip('/')}sdk/open-forms-sdk.<ext>",
        SDKRedirectView.as_view(),
    ),
]

# NOTE: The staticfiles_urlpatterns also discovers static files (i.e. no need to run collectstatic). Both the static
# folder and the media folder are only served via Django if DEBUG = True.
urlpatterns += staticfiles_urlpatterns() + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG and apps.is_installed("debug_toolbar"):  # pragma: no cover
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.DEBUG:  # pragma: nocover
    from openforms.registrations.contrib.email.views import EmailRegistrationTestView

    urlpatterns += [
        path(
            "api/drf-auth/",
            include("rest_framework.urls", namespace="rest_framework"),
        ),
        path(
            "dev/email/wrapper",
            EmailWrapperTestView.as_view(),
            name="dev-email-wrapper",
        ),
        path(
            "dev/email/digest",
            EmailWrapperTestView.as_view(),
            {"email_digest": True},
            name="dev-email-digest",
        ),
        path(
            "dev/email/confirmation/<int:submission_id>",
            EmailWrapperTestView.as_view(),
            name="dev-email-confirm",
        ),
        path(
            "dev/email/registration/<int:submission_id>",
            EmailRegistrationTestView.as_view(),
            name="dev-email-registration",
        ),
        path(
            "dev/submissions/<int:pk>/pdf",
            SubmissionPDFTestView.as_view(),
            name="dev-submissions-pdf",
        ),
    ]

if apps.is_installed("rosetta"):  # pragma: no cover
    urlpatterns = [path("admin/rosetta/", include("rosetta.urls"))] + urlpatterns

if apps.is_installed("silk"):  # pragma: no cover
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

# render a form detail page, as catch-all since it takes the slug of a form
urlpatterns += [
    path("", include("openforms.forms.urls", namespace="core")),
]
