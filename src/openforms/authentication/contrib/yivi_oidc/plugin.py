from typing import NotRequired, TypedDict

from django.contrib import auth
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.views import OIDCInit

from openforms.accounts.models import User
from openforms.forms.models import Form
from openforms.utils.urls import reverse_plus
from ..generic_oidc.plugin import OFOIDCPlugin

from ...base import BasePlugin, LoginLogo
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute, LogoAppearance
from ...registry import register
from ...typing import FormAuth
from .config import YiviOptions, YiviOptionsPolymorphicSerializer
from .constants import PLUGIN_ID
from .models import AvailableScope, YiviOpenIDConnectConfig

yivi_init = OIDCInit.as_view(
    config_class=YiviOpenIDConnectConfig,
    allow_next_from_query=False,
)


class YiviClaims(TypedDict):
    """
    Processed Yivi claims structure.

    See :attr:`openforms.authentication.yivi_oidc.models.CLAIMS_CONFIGURATION` for the source of this
    structure.

    None of the claims can be required, as they depend on the authAttribute used by the
    form.
    """

    # Claims for auth attribute bsn
    bsn_claim: NotRequired[str]

    # Claims for auth attribute kvk
    identifier_type_claim: NotRequired[str]
    legal_subject_claim: NotRequired[str]
    acting_subject_claim: NotRequired[str]
    branch_number_claim: NotRequired[str]

    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: NotRequired[str | int | float]


@register(PLUGIN_ID)
class YiviOIDCAuthentication(OFOIDCPlugin[YiviOptions]):
    """
    Authentication plugin using the global mozilla-django-oidc-db (as used for the admin)
    """

    session_key: str = "yivi_oidc"
    verbose_name = _("Yivi via OpenID Connect")
    # Yivi can provide a range of auth attributes, including bsn and kvk
    provides_auth = (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo)
    config_class = YiviOpenIDConnectConfig
    configuration_options = YiviOptionsPolymorphicSerializer

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: YiviOptions
    ):
        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query={"next": form_url},
        )

        response = yivi_init(request, return_url=return_url)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def transform_claims(
        self, options: YiviOptions, normalized_claims: YiviClaims
    ) -> FormAuth:
        form_auth = {
            "plugin": self.identifier,
            "attribute": options["authentication_attribute"],
            "additional_claims": {},
        }

        # Add claims resulted from additional scopes
        if (additional_scopes := options["additional_scopes"]) and len(
            additional_scopes
        ):
            claims_to_add = AvailableScope.objects.filter(
                scope__in=additional_scopes
            ).values_list("claims", flat=True)

            for claim in claims_to_add:
                form_auth["additional_claims"][claim] = (
                    normalized_claims[claim] if claim in normalized_claims else None
                )

        # Add authentication_attribute specific form auth properties
        match options["authentication_attribute"]:
            case AuthAttribute.bsn:
                # Coppied from digid_oidc
                form_auth["value"] = normalized_claims.get("bsn_claim", "")
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))
            case AuthAttribute.kvk:
                # Coppied from eherkenning_oidc
                form_auth["value"] = normalized_claims.get("legal_subject_claim", "")
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))
                form_auth["acting_subject_identifier_type"] = "opaque"
                form_auth["acting_subject_identifier_value"] = (
                    normalized_claims.get("acting_subject_claim")
                    or "dummy-set-by@openforms"
                )

                if service_restriction := normalized_claims.get(
                    "branch_number_claim", ""
                ):
                    form_auth["legal_subject_service_restriction"] = service_restriction
            case AuthAttribute.pseudo:
                # @TODO implement yivi pseudo auth
                pass

        return form_auth

    def handle_return(self, request, form, options: YiviOptions):
        """
        Redirect to form URL.
        """
        assert request.user.is_authenticated
        assert isinstance(request.user, User)

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: YiviClaims | None = request.session.get(self.session_key)
        if normalized_claims:
            request.session[FORM_AUTH_SESSION_KEY] = self.transform_claims(
                options, normalized_claims
            )

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        # @TODO not sure if this is right..?
        for key in (
            "oidc_id_token",
            "oidc_login_next",
            self.session_key,
        ):
            if key in request.session:
                del request.session[key]

        if request.user.is_authenticated:
            auth.logout(request)
            assert not request.user.is_authenticated

    def get_label(self):
        return "Yivi"

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/yivi.png")),
            href="https://yivi.app/",
            appearance=LogoAppearance.light,
        )
