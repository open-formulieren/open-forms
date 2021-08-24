from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm

from .models import OpenIDConnectPublicConfig


class OpenIDConnectPublicConfigForm(OpenIDConnectConfigForm):
    class Meta:
        model = OpenIDConnectPublicConfig
        fields = "__all__"
