from mozilla_django_oidc_db.mixins import SoloConfigMixin

import openforms.authentication.contrib.digid_oidc.settings as app_settings

from .models import OpenIDConnectPublicConfig


class SoloConfigMixin(SoloConfigMixin):
    config_class = OpenIDConnectPublicConfig

    def get_settings(self, attr, *args):
        if hasattr(app_settings, attr):
            return getattr(app_settings, attr)
        return super().get_settings(attr, *args)
