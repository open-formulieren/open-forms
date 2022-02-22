from mozilla_django_oidc_db.mixins import SoloConfigMixin

import openforms.authentication.contrib.digid_eherkenning_oidc.digid_settings as digid_settings
import openforms.authentication.contrib.digid_eherkenning_oidc.eherkenning_settings as eherkenning_settings

from .models import OpenIDConnectEHerkenningConfig, OpenIDConnectPublicConfig


class SoloConfigDigiDMixin(SoloConfigMixin):
    config_class = OpenIDConnectPublicConfig

    def get_settings(self, attr, *args):
        if hasattr(digid_settings, attr):
            return getattr(digid_settings, attr)
        return super().get_settings(attr, *args)


class SoloConfigEHerkenningMixin(SoloConfigMixin):
    config_class = OpenIDConnectEHerkenningConfig

    def get_settings(self, attr, *args):
        if hasattr(eherkenning_settings, attr):
            return getattr(eherkenning_settings, attr)
        return super().get_settings(attr, *args)
