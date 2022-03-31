from mozilla_django_oidc_db.mixins import SoloConfigMixin as _SoloConfigMixin

import digid_eherkenning_oidc_generics.digid_machtigen_settings as digid_machtigen_settings
import digid_eherkenning_oidc_generics.digid_settings as digid_settings
import digid_eherkenning_oidc_generics.eherkenning_settings as eherkenning_settings

from .models import (
    OpenIDConnectDigiDMachtigenConfig,
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)


class SoloConfigMixin(_SoloConfigMixin):
    config_class = ""
    settings_attribute = None

    def get_settings(self, attr, *args):
        if hasattr(self.settings_attribute, attr):
            return getattr(self.settings_attribute, attr)
        return super().get_settings(attr, *args)


class SoloConfigDigiDMixin(SoloConfigMixin):
    config_class = OpenIDConnectPublicConfig
    settings_attribute = digid_settings


class SoloConfigEHerkenningMixin(SoloConfigMixin):
    config_class = OpenIDConnectEHerkenningConfig
    settings_attribute = eherkenning_settings


class SoloConfigDigiDMachtigenMixin(SoloConfigMixin):
    config_class = OpenIDConnectDigiDMachtigenConfig
    settings_attribute = digid_machtigen_settings
