import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from .utils import obfuscate_claim

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(_OIDCAuthenticationBackend):
    session_key = ""
    claim_name_field = "identifier_claim_name"

    def get_or_create_user(self, access_token, id_token, payload):
        user_info = self.get_userinfo(access_token, id_token, payload)
        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        self.request.session[self.session_key] = payload[
            self.get_settings(self.claim_name_field)
        ]
        user = AnonymousUser()
        user.is_active = True
        return user

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""
        # TODO configurable sensitive claims?
        obfuscated_claims = {
            k: obfuscate_claim(v) if k == self.config.identifier_claim_name else v
            for k, v in claims.items()
        }
        logger.debug("OIDC claims received: %s", obfuscated_claims)

        if (claim_name := self.get_settings(self.claim_name_field)) not in claims:
            logger.error(
                "`identifier_claim_name=%s` not in OIDC claims, cannot proceed with authentication",
                claim_name,
            )
            return False
        return True
