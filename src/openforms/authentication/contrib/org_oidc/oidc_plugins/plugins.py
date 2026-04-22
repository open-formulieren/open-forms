from typing import override

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
