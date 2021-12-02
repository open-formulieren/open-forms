from typing import Optional

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


@register("digid-mock")
class DigidMockAuthentication(BasePlugin):
    verbose_name = _("DigiD Mock")
    provides_auth = AuthAttribute.bsn
    is_demo_plugin = True

    def start_login(self, request, form, form_url):
        url = reverse("digid-mock:login", request=request)
        params = {
            "acs": self.get_return_url(request, form),
            "next": form_url,
            "cancel": form_url,
        }
        url = f"{url}?{urlencode(params)}"
        return HttpResponseRedirect(url)

    def handle_return(self, request, form):
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        bsn = request.GET.get("bsn")
        if not bsn:
            return HttpResponseBadRequest("missing 'bsn' parameter")

        request.session["form_auth"] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": bsn,
        }
        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/digid-46x46.png")),
            href="https://www.digid.nl/",
        )
