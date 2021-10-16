from typing import Optional

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.translation import gettext_lazy as _

from openforms.authentication.base import LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.contrib.eherkenning.plugin import AuthenticationBasePlugin
from openforms.authentication.registry import register


@register("eidas")
class EIDASAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eIDAS")
    provides_auth = AuthAttribute.pseudo

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eidas.png")),
            href="https://digital-strategy.ec.europa.eu/en/policies/eu-trust-mark",
        )
