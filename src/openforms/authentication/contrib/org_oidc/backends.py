from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from .mixins import SoloConfigMixin


class OIDCAuthenticationBackend(SoloConfigMixin, _OIDCAuthenticationBackend):
    @classmethod
    def get_import_path(cls):
        # needed for auth.login()/auth.logout()
        return f"{cls.__module__}.{cls.__qualname__}"
