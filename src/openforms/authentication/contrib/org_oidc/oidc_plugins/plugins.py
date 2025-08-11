import warnings
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from mozilla_django_oidc_db.plugins import OIDCAdminPlugin
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.schemas import ADMIN_OPTIONS_SCHEMA
from mozilla_django_oidc_db.typing import JSONObject

from openforms.contrib.auth_oidc.plugin import OFBaseOIDCPluginProtocol

from ..views import callback_view
from .constants import OIDC_ORG_IDENTIFIER


@register(OIDC_ORG_IDENTIFIER)
class OIDCOrgPlugin(OIDCAdminPlugin, OFBaseOIDCPluginProtocol):  # pyright: ignore[reportGeneralTypeIssues] # TODO: OIDCAdminPlugin is a decorated class
    def get_schema(self) -> JSONObject:
        return ADMIN_OPTIONS_SCHEMA

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return callback_view(request)  # pyright: ignore[reportReturnType] # .as_view() returns HttpResponseBase

    def _get_legacy_callback(self) -> str:
        return "org-oidc-callback"

    def get_setting(self, attr: str, *args) -> Any:
        attr_lower = attr.lower()

        if attr_lower == "oidc_authentication_callback_url":
            if settings.USE_LEGACY_ORG_OIDC_ENDPOINTS:
                warnings.warn(
                    "Legacy OIDC callback endpoints will be removed in 4.0",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return self._get_legacy_callback()
            return "oidc_authentication_callback"

        return super().get_setting(attr, *args)
