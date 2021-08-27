from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm

from .models import OpenIDConnectEHerkenningConfig


class OpenIDConnectEHerkenningConfigForm(OpenIDConnectConfigForm):
    class Meta:
        model = OpenIDConnectEHerkenningConfig
        fields = "__all__"
