import warnings
from typing import Any, override

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase

from mozilla_django_oidc_db.plugins import OIDCAdminPlugin
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.schemas import ADMIN_OPTIONS_SCHEMA
from mozilla_django_oidc_db.typing import JSONObject

from ..views import callback_view
from .constants import OIDC_ORG_IDENTIFIER


@register(OIDC_ORG_IDENTIFIER)
class OIDCOrgPlugin(OIDCAdminPlugin):
    @override
    def get_schema(self) -> JSONObject:
        return ADMIN_OPTIONS_SCHEMA

    @override
    def handle_callback(self, request: HttpRequest) -> HttpResponseBase:
        return callback_view(request)

    @override
    def get_setting(self, attr: str, *args) -> Any:
        attr_lower = attr.lower()

        if attr_lower == "oidc_authentication_callback_url":
            if settings.USE_LEGACY_ORG_OIDC_ENDPOINTS:
                warnings.warn(
                    "Legacy OIDC callback endpoints will be removed in 4.0",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return "org-oidc-callback"
            return "oidc_authentication_callback"

        return super().get_setting(attr, *args)
