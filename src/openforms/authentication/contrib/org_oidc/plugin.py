from django.contrib import auth
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext, gettext_lazy as _

from mozilla_django_oidc_db.views import OIDCAuthenticationRequestInitView

from openforms.accounts.models import User
from openforms.forms.models import Form
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin, LoginLogo
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute, LogoAppearance
from ...registry import register
from .config import OIDCOptions, OIDCOptionsSerializer
from .oidc_plugins.constants import OIDC_ORG_IDENTIFIER

PLUGIN_IDENTIFIER = "org-oidc"

org_oidc_init = OIDCAuthenticationRequestInitView.as_view(
    identifier=OIDC_ORG_IDENTIFIER,
    allow_next_from_query=False,
)


@register(PLUGIN_IDENTIFIER)
class OIDCAuthentication(BasePlugin[OIDCOptions]):
    """
    Authentication plugin using the global mozilla-django-oidc-db (as used for the admin)
    """

    verbose_name = _("Organization via OpenID Connect")
    provides_auth = (AuthAttribute.employee_id,)
    oidc_plugin_identifier = OIDC_ORG_IDENTIFIER
    init_view = staticmethod(org_oidc_init)
    configuration_options = OIDCOptionsSerializer

    def start_login(self, request: HttpRequest, form: Form, form_url: str, options):
        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query={"next": form_url},
        )
        if request.user.is_authenticated:
            # logout user if logged in with other account
            # this is relevant when staff users are already logged in, the OIDC
            # state/redirects get confused, and could send the user back to the admin
            # instead of the form. # this is likely because it picks a .success_url
            # instead of session data
            auth.logout(request)

        response = self.init_view(request, return_url=return_url)

        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_return(self, request, form, options):
        """
        Redirect to form URL.
        """
        assert request.user.is_authenticated
        assert isinstance(request.user, User)

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth[0],
            "value": request.user.employee_id or request.user.username,
        }

        # we could render here but let's redirect
        return HttpResponseRedirect(
            self.get_registrator_subject_url(request, form, form_url)
        )

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
        return gettext("OpenID Connect")

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/openid.png")),
            href="https://openid.net/",
            appearance=LogoAppearance.light,
        )


assert len(OIDCAuthentication.provides_auth) == 1
