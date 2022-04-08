from copy import deepcopy

from django import forms
from django.core.validators import ValidationError
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.constants import OIDC_MAPPING as _OIDC_MAPPING
from mozilla_django_oidc_db.forms import CleanUrlsFormMixin, OpenIDConnectConfigForm

from openforms.forms.models import Form

from .models import OpenIDConnectEHerkenningConfig, OpenIDConnectPublicConfig

OIDC_MAPPING = deepcopy(_OIDC_MAPPING)

OIDC_MAPPING["oidc_op_logout_endpoint"] = "end_session_endpoint"


class OIDCGenericConfigForm(CleanUrlsFormMixin, forms.ModelForm):
    required_endpoints = [
        "oidc_op_authorization_endpoint",
        "oidc_op_token_endpoint",
        "oidc_op_user_endpoint",
        "oidc_op_logout_endpoint",
    ]
    oidc_mapping = OIDC_MAPPING


# class OpenIDConnectBaseConfigForm(OpenIDConnectConfigForm):
#     required_endpoints = [
#         "oidc_op_authorization_endpoint",
#         "oidc_op_token_endpoint",
#         "oidc_op_user_endpoint",
#         "oidc_op_logout_endpoint",
#     ]
#     oidc_mapping = OIDC_MAPPING
#     plugin_identifier = ""
#
#     def clean_enabled(self):
#         enabled = self.cleaned_data["enabled"]
#
#         if not enabled:
#             forms_with_backend = Form.objects.filter(
#                 authentication_backends__contains=[self.plugin_identifier]
#             )
#
#             if forms_with_backend.exists():
#                 raise ValidationError(
#                     _(
#                         "{plugin_identifier} is selected as authentication backend "
#                         "for one or more forms, please remove this backend from these "
#                         "forms before disabling this authentication backend."
#                     ).format(plugin_identifier=self.plugin_identifier)
#                 )
#         return enabled


class OpenIDConnectPublicConfigForm(forms.ModelForm):
    class Meta:
        model = OpenIDConnectPublicConfig
        fields = "__all__"


class OpenIDConnectEHerkenningConfigForm(forms.ModelForm):
    class Meta:
        model = OpenIDConnectEHerkenningConfig
        fields = "__all__"
