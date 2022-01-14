from mozilla_django_oidc_db.mixins import SoloConfigMixin

import openforms.authentication.contrib.eherkenning_oidc.settings as app_settings

from .models import OpenIDConnectEHerkenningConfig


class SoloConfigMixin(SoloConfigMixin):
    config_class = OpenIDConnectEHerkenningConfig

    def get_settings(self, attr, *args):
        if hasattr(app_settings, attr):
            return getattr(app_settings, attr)
        return super().get_settings(attr, *args)
