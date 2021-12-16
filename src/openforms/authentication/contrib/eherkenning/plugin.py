from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework.reverse import reverse

from openforms.forms.models import Form

from ...base import BasePlugin, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .constants import EHERKENNING_AUTH_SESSION_KEY, EIDAS_AUTH_SESSION_KEY  # noqa


class AuthenticationBasePlugin(BasePlugin):
    session_key = None

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
        return_url = furl(auth_return_url).set(
            {
                "next": form_url,
            }
        )
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url.args[CO_SIGN_PARAMETER] = co_sign_param

        redirect_url = furl(login_url).set(
            {
                "next": str(return_url),
                "attr_consuming_service_index": self._get_attr_consuming_service_index(),
            }
        )
        return HttpResponseRedirect(str(redirect_url))

    def handle_co_sign(
        self, request: HttpRequest, form: Form
    ) -> Optional[Dict[str, Any]]:
        if not (identifier := request.session.get(self.session_key)):
            raise InvalidCoSignData(
                f"Missing or empty auth session data (key: {self.session_key})"
            )
        return {
            "identifier": identifier,
            "fields": {},
        }

    def handle_return(self, request: HttpRequest, form: Form):
        """
        Redirect (back) to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        # set by the view :class:`.views.eHerkenningAssertionConsumerServiceView` after
        # valid eHerkenning/EIDAS login
        identifier = request.session.get(self.session_key)

        # set the session auth key only if we're not co-signing
        if identifier and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth,
                "value": identifier,
            }

        return HttpResponseRedirect(form_url)


@register("eherkenning")
class EHerkenningAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eHerkenning")
    provides_auth = AuthAttribute.kvk
    session_key = EHERKENNING_AUTH_SESSION_KEY

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eherkenning.svg")),
            href="https://www.eherkenning.nl/",
        )


@register("eidas")
class EIDASAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eIDAS")
    provides_auth = AuthAttribute.pseudo
    session_key = EIDAS_AUTH_SESSION_KEY

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eidas.png")),
            href="https://digital-strategy.ec.europa.eu/en/policies/eu-trust-mark",
        )
