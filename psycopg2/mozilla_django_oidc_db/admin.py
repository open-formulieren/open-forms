from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .forms import OpenIDConnectConfigForm
from .models import OpenIDConnectConfig


@admin.register(OpenIDConnectConfig)
class OpenIDConnectConfigAdmin(DynamicArrayMixin, SingletonModelAdmin):
    form = OpenIDConnectConfigForm
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
                )
            },
        ),
        (
            _("User profile"),
            {
                "fields": (
                    "groups_claim",
                    "claim_mapping",
                    "sync_groups",
                    "make_users_staff",
                )
            },
        ),
    )
