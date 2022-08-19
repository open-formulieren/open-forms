import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(_OIDCAuthenticationBackend):
    session_key = ""
    config_identifier_field = "identifier_claim_name"

    def extract_claims(self, payload):
        self.request.session[self.session_key] = self.retrieve_identifier_claim(payload)

    def get_or_create_user(self, access_token, id_token, payload):
        user_info = self.get_userinfo(access_token, id_token, payload)
        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        self.extract_claims(payload)

        user = AnonymousUser()
        user.is_active = True
        return user
