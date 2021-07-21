from typing import Optional

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


@register("digid")
class DigidAuthentication(BasePlugin):
    verbose_name = _("Digid")
    provides_auth = AuthAttribute.bsn

    def start_login(self, request, form, form_url):
        """Redirect to the /digid/login endpoint to start step 2 of the authentication

        https://www.logius.nl/sites/default/files/public/bestanden/diensten/DigiD/Koppelvlakspecificatie-SAML-DigiD.pdf
        """
        login_url = reverse("digid:login", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "digid"},
        )
        params = {"next": form_url}
        return_url = f"{auth_return_url}?{urlencode(params)}"

        auth_return_params = {"next": return_url}
        url = f"{login_url}?{urlencode(auth_return_params)}"

        return HttpResponseRedirect(url)

    def handle_return(self, request, form):
        """Redirect to form URL.

        This is called after step 7 of the authentication is finished
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")
        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/digid-46x46.png")),
            href="https://www.digid.nl/",
        )
