from typing import Optional

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


@register("eherkenning")
class EHerkenningAuthentication(BasePlugin):
    verbose_name = _("eHerkenning")
    provides_auth = AuthAttribute.kvk

    def start_login(self, request, form, form_url):
        """Redirect to the /eherkenning/login endpoint to start the authentication"""
        login_url = reverse("eherkenning:login", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        return_url = f"{auth_return_url}?next={form_url}"

        auth_return_params = {"next": return_url, "attr_consuming_service_index": "1"}
        url = f"{login_url}?{urlencode(auth_return_params)}"
        return HttpResponseRedirect(url)

    def handle_return(self, request, form):
        """Redirect to form URL."""
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")
        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eherkenning.svg")),
            href="https://www.eherkenning.nl/",
        )
