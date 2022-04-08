from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .forms import (
    OIDCGenericConfigForm,
    OpenIDConnectEHerkenningConfigForm,
    OpenIDConnectPublicConfigForm,
)
from .models import (
    OpenIDConnectBaseConfig,
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)


class OpenIDConnectGenericAdmin(DynamicArrayMixin, SingletonModelAdmin):
    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
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
    )


class OpenIDConnectClientConfigAdmin(DynamicArrayMixin, SingletonModelAdmin):
    fieldsets = (
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
                )
            },
        ),
        (_("Keycloak specific settings"), {"fields": ("oidc_keycloak_idp_hint",)}),
    )


@admin.register(OpenIDConnectBaseConfig)
class OIDCGenericConfigAdmin(OpenIDConnectGenericAdmin):
    form = OIDCGenericConfigForm


@admin.register(OpenIDConnectPublicConfig)
class OpenIDConnectConfigDigiDAdmin(OpenIDConnectClientConfigAdmin):
    form = OpenIDConnectPublicConfigForm


@admin.register(OpenIDConnectEHerkenningConfig)
class OpenIDConnectConfigEHerkenningAdmin(OpenIDConnectClientConfigAdmin):
    form = OpenIDConnectEHerkenningConfigForm
