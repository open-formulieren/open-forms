import logging

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from openforms.authentication.contrib.org_oidc.constants import OIDC_AUTH_SESSION_KEY
from openforms.authentication.contrib.org_oidc.mixins import SoloConfigMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(SoloConfigMixin, _OIDCAuthenticationBackend):
    session_key = OIDC_AUTH_SESSION_KEY
    config_identifier_field = "username_claim"

    def extract_claims(self, payload):
        self.request.session[self.session_key] = self.retrieve_identifier_claim(payload)

    def get_or_create_user(self, access_token, id_token, payload):
        user = super().get_or_create_user(access_token, id_token, payload)

        if user:
            self.extract_claims(payload)

        return user

    @classmethod
    def get_import_path(cls):
        # needed for auth.login()/auth.logout()
        return f"{cls.__module__}.{cls.__qualname__}"
