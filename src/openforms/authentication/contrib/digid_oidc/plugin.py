from typing import Optional

from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register
from openforms.forms.models import Form


@register("digid_oidc")
class DigiDOIDCAuthentication(BasePlugin):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = AuthAttribute.bsn

    def get_start_url(self, request: HttpRequest, form: Form) -> str:
        return request.build_absolute_uri(
            reverse(
                "digid_oidc:oidc_authentication_init",
            )
        )

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/digid-46x46.png")),
            href="https://www.digid.nl/",
        )
