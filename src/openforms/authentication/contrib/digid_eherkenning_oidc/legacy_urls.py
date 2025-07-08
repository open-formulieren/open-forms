"""
Callback URLs for the different plugins.

These plugin-specific callback URLs are deprecated and will be removed in Open Forms
3.0. Instead, use the generic callback URL in urls.py - it can handle the different
configs.
"""

from django.urls import include, path

from mozilla_django_oidc_db.views import OIDCCallbackView

oidc_callback = OIDCCallbackView.as_view()

urlpatterns = [
    path(
        "digid-oidc/",
        include(
            (
                [
                    path("callback/", oidc_callback, name="callback"),
                ],
                "digid_oidc",
            )
        ),
    ),
    path(
        "eherkenning-oidc/",
        include(
            (
                [
                    path("callback/", oidc_callback, name="callback"),
                ],
                "eherkenning_oidc",
            )
        ),
    ),
    path(
        "digid-machtigen-oidc/",
        include(
            (
                [
                    path("callback/", oidc_callback, name="callback"),
                ],
                "digid_machtigen_oidc",
            )
        ),
    ),
    path(
        "eherkenning-bewindvoering-oidc/",
        include(
            (
                [
                    path("callback/", oidc_callback, name="callback"),
                ],
                "eherkenning_bewindvoering_oidc",
            )
        ),
    ),
]
