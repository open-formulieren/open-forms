import json

from django import forms
from django.utils.translation import gettext_lazy as _

import requests

from .constants import OIDC_MAPPING, OPEN_ID_CONFIG_PATH
from .models import OpenIDConnectConfig


class OpenIDConnectConfigForm(forms.ModelForm):
    class Meta:
        model = OpenIDConnectConfig
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["oidc_op_authorization_endpoint"].required = False
        self.fields["oidc_op_token_endpoint"].required = False
        self.fields["oidc_op_user_endpoint"].required = False

    def clean(self):
        cleaned_data = super().clean()

        discovery_endpoint = cleaned_data.get("oidc_op_discovery_endpoint")

        # Derive the endpoints from the discovery endpoint
        if discovery_endpoint:
            try:
                response = requests.get(
                    f"{discovery_endpoint}{OPEN_ID_CONFIG_PATH}", timeout=10
                )
                configuration = response.json()

                for model_attr, oidc_attr in OIDC_MAPPING.items():
                    cleaned_data[model_attr] = configuration.get(oidc_attr)
            except (
                requests.exceptions.RequestException,
                json.decoder.JSONDecodeError,
            ):
                raise forms.ValidationError(
                    {
                        "oidc_op_discovery_endpoint": _(
                            "Something went wrong while retrieving the configuration."
                        )
                    }
                )
        else:
            required_endpoints = [
                "oidc_op_authorization_endpoint",
                "oidc_op_token_endpoint",
                "oidc_op_user_endpoint",
            ]
            for field in required_endpoints:
                if not cleaned_data.get(field):
                    self.add_error(field, _("This field is required."))

        return cleaned_data
