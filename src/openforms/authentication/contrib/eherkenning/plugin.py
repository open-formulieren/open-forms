from typing import Optional

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse

from openforms.forms.models import Form

from ...base import BasePlugin, LoginLogo
from ...constants import AuthAttribute
from ...registry import register


class AuthenticationBasePlugin(BasePlugin):
    def _get_attr_consuming_service_index(self) -> str:
        indices = {
            "eidas": settings.EIDAS_SERVICE_INDEX,
            "eherkenning": settings.EHERKENNING_SERVICE_INDEX,
        }
        return indices[self.identifier]

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> HttpResponseRedirect:
        """
        Redirect to the /eherkenning/login endpoint to start the authentication.

        The distinction between the eIDAS and eHerkenning flow is determined by the
        ``AttributeConsumingServiceIndex``.
        """
        login_url = reverse("eherkenning:login", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
        )
        return_url = f"{auth_return_url}?next={form_url}"

        auth_return_params = {
            "next": return_url,
            "attr_consuming_service_index": self._get_attr_consuming_service_index(),
        }
        url = f"{login_url}?{urlencode(auth_return_params)}"
        return HttpResponseRedirect(url)

    def handle_return(self, request: HttpRequest, form: Form):
        """Redirect to form URL."""
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")
        return HttpResponseRedirect(form_url)


@register("eherkenning")
class EHerkenningAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eHerkenning")
    provides_auth = AuthAttribute.kvk

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eherkenning.svg")),
            href="https://www.eherkenning.nl/",
        )
