from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .forms import (
    OpenIDConnectDigiDMachtigenConfigForm,
    OpenIDConnectEHerkenningBewindvoeringConfigForm,
    OpenIDConnectEHerkenningConfigForm,
    OpenIDConnectPublicConfigForm,
)
from .models import (
    OpenIDConnectDigiDMachtigenConfig,
    OpenIDConnectEHerkenningBewindvoeringConfig,
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)


class OpenIDConnectConfigBaseAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
        ),
        (
            _("Common settings"),
            {
                "fields": (
                    "identifier_claim_name",
                    "oidc_rp_client_id",
                    "oidc_rp_client_secret",
                    "oidc_rp_scopes_list",
                    "oidc_rp_sign_algo",
                    "oidc_rp_idp_sign_key",
                    "userinfo_claims_source",
                )
            },
        ),
        (
            _("Endpoints"),
            {
                "fields": (
                    "oidc_op_discovery_endpoint",
                    "oidc_op_jwks_endpoint",
                    "oidc_op_authorization_endpoint",
                    "oidc_op_token_endpoint",
                    "oidc_op_user_endpoint",
                    "oidc_op_logout_endpoint",
                )
            },
        ),
        (_("Keycloak specific settings"), {"fields": ("oidc_keycloak_idp_hint",)}),
    )


@admin.register(OpenIDConnectPublicConfig)
class OpenIDConnectConfigDigiDAdmin(OpenIDConnectConfigBaseAdmin):
    form = OpenIDConnectPublicConfigForm


@admin.register(OpenIDConnectEHerkenningConfig)
class OpenIDConnectConfigEHerkenningAdmin(OpenIDConnectConfigBaseAdmin):
    form = OpenIDConnectEHerkenningConfigForm


@admin.register(OpenIDConnectDigiDMachtigenConfig)
class OpenIDConnectConfigDigiDMachtigenAdmin(SingletonModelAdmin):
    form = OpenIDConnectDigiDMachtigenConfigForm

    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
        ),
        (
            _("Common settings"),
            {
                "fields": (
                    "oidc_rp_client_id",
                    "oidc_rp_client_secret",
                    "oidc_rp_scopes_list",
                    "oidc_rp_sign_algo",
                    "oidc_rp_idp_sign_key",
                    "userinfo_claims_source",
                )
            },
        ),
        (
            _("Attributes to extract from claim"),
            {
                "fields": (
                    "vertegenwoordigde_claim_name",
                    "gemachtigde_claim_name",
                )
            },
        ),
        (
            _("Endpoints"),
            {
                "fields": (
                    "oidc_op_discovery_endpoint",
                    "oidc_op_jwks_endpoint",
                    "oidc_op_authorization_endpoint",
                    "oidc_op_token_endpoint",
                    "oidc_op_user_endpoint",
                    "oidc_op_logout_endpoint",
                )
            },
        ),
        (_("Keycloak specific settings"), {"fields": ("oidc_keycloak_idp_hint",)}),
    )


@admin.register(OpenIDConnectEHerkenningBewindvoeringConfig)
class OpenIDConnectConfigEHerkenningBewindvoeringAdmin(SingletonModelAdmin):
    form = OpenIDConnectEHerkenningBewindvoeringConfigForm

    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
        ),
        (
            _("Common settings"),
            {
                "fields": (
                    "oidc_rp_client_id",
                    "oidc_rp_client_secret",
                    "oidc_rp_scopes_list",
                    "oidc_rp_sign_algo",
                    "oidc_rp_idp_sign_key",
                    "userinfo_claims_source",
                )
            },
        ),
        (
            _("Attributes to extract from claim"),
            {
                "fields": (
                    "vertegenwoordigde_company_claim_name",
                    "gemachtigde_person_claim_name",
                )
            },
        ),
        (
            _("Endpoints"),
            {
                "fields": (
                    "oidc_op_discovery_endpoint",
                    "oidc_op_jwks_endpoint",
                    "oidc_op_authorization_endpoint",
                    "oidc_op_token_endpoint",
                    "oidc_op_user_endpoint",
                    "oidc_op_logout_endpoint",
                )
            },
        ),
        (_("Keycloak specific settings"), {"fields": ("oidc_keycloak_idp_hint",)}),
    )
