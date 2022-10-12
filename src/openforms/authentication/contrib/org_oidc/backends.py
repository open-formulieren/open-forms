import logging

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from .mixins import SoloConfigMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(SoloConfigMixin, _OIDCAuthenticationBackend):
    config_identifier_field = "username_claim"

    @classmethod
    def get_import_path(cls):
        # needed for auth.login()/auth.logout()
        return f"{cls.__module__}.{cls.__qualname__}"
