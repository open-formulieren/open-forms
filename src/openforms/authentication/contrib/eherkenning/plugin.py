import logging
from typing import Any, NoReturn

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import AssuranceLevels
from digid_eherkenning.models import EherkenningConfiguration
from furl import furl
from rest_framework.reverse import reverse

from openforms.contrib.digid_eherkenning.utils import get_eherkenning_logo
from openforms.forms.models import Form

from ...base import BasePlugin, LoginLogo
from ...constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    AuthAttribute,
    LogoAppearance,
)
from ...exceptions import InvalidCoSignData
from ...registry import register
from .constants import (
    EHERKENNING_AUTH_SESSION_AUTHN_CONTEXTS,
    EHERKENNING_AUTH_SESSION_KEY,
    EHERKENNING_BRANCH_NUMBERS_SESSION_KEY,
    EIDAS_AUTH_SESSION_KEY,
)

logger = logging.getLogger(__name__)

_LOA_ORDER = [loa.value for loa in AssuranceLevels]


def loa_order(loa: str) -> int:
    # higher are defined later in the enum
    return -1 if loa not in _LOA_ORDER else _LOA_ORDER.index(loa)


class AuthenticationBasePlugin(BasePlugin):
    session_key: str

    def _get_attr_consuming_service_index(self) -> str:
        config = EherkenningConfiguration.get_solo()
        indices = {
            "eherkenning": config.eh_attribute_consuming_service_index,
            "eidas": config.eidas_attribute_consuming_service_index,
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
    ) -> dict[str, Any] | NoReturn:
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
                "loa": self.get_session_loa(request.session),
                **self.get_extra_form_auth_kwargs(request.session),
            }

        return HttpResponseRedirect(form_url)

    def get_session_loa(self, session):
        return ""

    def get_extra_form_auth_kwargs(self, session) -> dict[str, Any]:
        return {}

    def logout(self, request: HttpRequest):
        if self.session_key in request.session:
            del request.session[self.session_key]


@register("eherkenning")
class EHerkenningAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eHerkenning")
    provides_auth = AuthAttribute.kvk
    session_key = EHERKENNING_AUTH_SESSION_KEY

    def get_session_loa(self, session) -> str:
        authn_contexts = session.get(EHERKENNING_AUTH_SESSION_AUTHN_CONTEXTS, [""])
        return max(authn_contexts, key=loa_order)

    def get_extra_form_auth_kwargs(self, session) -> dict[str, Any]:
        branch_numbers = session.get(EHERKENNING_BRANCH_NUMBERS_SESSION_KEY)
        if not branch_numbers:
            return {}
        if (num := len(branch_numbers)) > 1:
            # https://afsprakenstelsel.etoegang.nl/Startpagina/v2/interface-specifications-dv-hm
            # explicitly mentions that "one or more ServiceRestrictions" can be provided,
            # we currently only support one.
            logger.warning(
                "Got more than one branch number (got %d), this is unexpected!",
                num,
            )
        branch_number = branch_numbers[0]
        return {"legal_subject_service_restriction": branch_number}

    def check_requirements(self, request, config):
        # check LoA requirements
        authenticated_loa = request.session[FORM_AUTH_SESSION_KEY]["loa"]
        required = EherkenningConfiguration.get_solo().eh_loa
        return loa_order(authenticated_loa) >= loa_order(required)

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))


@register("eidas")
class EIDASAuthentication(AuthenticationBasePlugin):
    verbose_name = _("eIDAS")
    provides_auth = AuthAttribute.pseudo
    session_key = EIDAS_AUTH_SESSION_KEY

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eidas.png")),
            href="https://digital-strategy.ec.europa.eu/en/policies/eu-trust-mark",
            appearance=LogoAppearance.light,
        )
