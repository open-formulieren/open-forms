from django.contrib import auth
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.authentication.registry import register
from openforms.forms.models import Form


@register("org-oidc")
class OIDCAuthentication(BasePlugin):
    """
    Authentication plugin using the global mozilla-django-oidc-db (as used for the admin)
    """

    verbose_name = _("Organisation via OpenID Connect")
    provides_auth = AuthAttribute.employee_id

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        login_url = reverse("org-oidc:init", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
        )
        return_url = furl(auth_return_url).set(
            {
                "next": form_url,
            }
        )

        redirect_url = furl(login_url).set({"next": str(return_url)})
        return HttpResponseRedirect(str(redirect_url))

    def handle_return(self, request, form):
        """
        Redirect to form URL.
        """
        assert request.user.is_authenticated

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": request.user.username,
        }

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        for key in (
            "oidc_id_token",
            "oidc_login_next",
            "oidc_states",
        ):
            if key in request.session:
                del request.session[key]

        if request.user.is_authenticated:
            auth.logout(request)
            assert not request.user.is_authenticated

    def get_label(self):
        return _("OpenID Connect")

    def get_logo(self, request: HttpRequest):
        return {
            "image_src": request.build_absolute_uri(static("img/openid.png")),
            "href": "https://openid.net/",
        }
