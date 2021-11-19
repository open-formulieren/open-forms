from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .forms import OpenIDConnectPublicConfigForm
from .models import OpenIDConnectPublicConfig


@admin.register(OpenIDConnectPublicConfig)
class OpenIDConnectConfigAdmin(DynamicArrayMixin, SingletonModelAdmin):
    """
    Adapted from mozilla-django-oidc-db, removing unnecessary fields
    """

    form = OpenIDConnectPublicConfigForm
    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
        ),
        (
            _("Common settings"),
            {
                "fields": (
                    "bsn_claim_name",
                    "oidc_rp_client_id",
                    "oidc_rp_client_secret",
                    "oidc_rp_scopes_list",
                    "oidc_rp_sign_algo",
                    "oidc_rp_idp_sign_key",
                    "oidc_redirect_allowed_hosts",
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
