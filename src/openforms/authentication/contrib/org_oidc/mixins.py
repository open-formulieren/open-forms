from mozilla_django_oidc_db.mixins import SoloConfigMixin as _SoloConfigMixin
from mozilla_django_oidc_db.models import OpenIDConnectConfig


class SoloConfigMixin(_SoloConfigMixin):
    config_class = OpenIDConnectConfig

    plugin_identifier = "org-oidc"
    oidc_authentication_callback_url = "org-oidc:callback"

    def get_settings(self, attr, *args):
        attr_lowercase = attr.lower()
        if hasattr(self, attr_lowercase):
            return getattr(self, attr_lowercase)
        return super().get_settings(attr, *args)
