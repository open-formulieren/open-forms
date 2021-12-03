from typing import Optional

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework.reverse import reverse

from ...base import BasePlugin, LoginLogo
from ...constants import CO_SIGN_PARAMETER, AuthAttribute
from ...registry import register


@register("digid")
class DigidAuthentication(BasePlugin):
    verbose_name = _("DigiD")
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
        return_url = furl(auth_return_url).set(
            {
                "next": form_url,
            }
        )
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url.args[CO_SIGN_PARAMETER] = co_sign_param

        redirect_url = furl(login_url).set({"next": str(return_url)})
        return HttpResponseRedirect(str(redirect_url))

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
