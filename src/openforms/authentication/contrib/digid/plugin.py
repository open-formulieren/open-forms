from typing import Optional

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.registry import register


@register("digid")
class DigidAuthentication(BasePlugin):
    verbose_name = _("Digid")

    def start_login(self, request, form, form_url):
        """Redirect to the /digid/login endpoint to start step 2 of the authentication

        https://www.logius.nl/sites/default/files/public/bestanden/diensten/DigiD/Koppelvlakspecificatie-SAML-DigiD.pdf
        """
        url = reverse("digid:login", request=request)
        params = {"next": form_url}
        url = f"{url}?{urlencode(params)}"
        return HttpResponseRedirect(url)

    # This could maybe be removed completely and let .views.DigiDAssertionConsumerServiceView
    # return directly to the form URL
    def handle_return(self, request, form):
        """Redirect to form URL.

        This is called after step 7 of the authentication is finished
        """
        form_url = reverse("core:form-detail", kwargs={"slug": form.slug})
        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/digid-46x46.png")),
            href="https://www.digid.nl/",
        )
