from mozilla_django_oidc.utils import import_from_settings

from .models import OpenIDConnectConfig


class SoloConfigMixin:
    @staticmethod
    def get_settings(attr, *args):
        config = OpenIDConnectConfig.get_solo()
        attr_lowercase = attr.lower()
        if getattr(config, attr_lowercase, ""):
            return getattr(config, attr_lowercase)
        return import_from_settings(attr, *args)
