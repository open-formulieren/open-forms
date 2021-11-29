from typing import Optional
from urllib.parse import urlencode

from django.db import OperationalError
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

import requests
from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register
from openforms.forms.models import Form

from .models import OpenIDConnectEHerkenningConfig


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(BasePlugin):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.bsn

    def get_start_url(self, request: HttpRequest, form: Form) -> str:
        return request.build_absolute_uri(
            reverse(
                "eherkenning_oidc:oidc_authentication_init",
            )
        )

    def logout(self, request: HttpRequest):
        params = urlencode({"id_token_hint": request.session["oidc_id_token"]})
        logout_endpoint = (
            OpenIDConnectEHerkenningConfig.get_solo().oidc_op_logout_endpoint
        )
        requests.get(f"{logout_endpoint}?{params}")

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eherkenning.svg")),
            href="https://www.eherkenning.nl/",
        )

    @property
    def is_enabled(self):
        try:
            config = OpenIDConnectEHerkenningConfig.get_solo()
            return config.enabled
        except OperationalError:
            return False
