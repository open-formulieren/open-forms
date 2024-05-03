from typing import Any

from mozilla_django_oidc.utils import import_from_settings

from .models import OpenIDConnectBaseConfig


def get_setting_from_config(config: OpenIDConnectBaseConfig, attr: str, *args) -> Any:
    """
    Look up a setting from the config record or fall back to Django settings.

    TODO: port this into mozilla_django_oidc_db.
    """
    attr_lowercase = attr.lower()
    if hasattr(config, attr_lowercase):
        # Workaround for OIDC_RP_IDP_SIGN_KEY being an empty string by default.
        # mozilla-django-oidc explicitly checks if `OIDC_RP_IDP_SIGN_KEY` is not `None`
        # https://github.com/mozilla/mozilla-django-oidc/blob/master/mozilla_django_oidc/auth.py#L189
        if (value_from_config := getattr(config, attr_lowercase)) == "":
            return None
        return value_from_config
    return import_from_settings(attr, *args)
