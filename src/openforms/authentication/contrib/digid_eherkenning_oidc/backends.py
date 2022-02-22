import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse

from mozilla_django_oidc_db.backends import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from .constants import DIGID_OIDC_AUTH_SESSION_KEY, EHERKENNING_OIDC_AUTH_SESSION_KEY
from .mixins import SoloConfigDigiDMixin, SoloConfigEHerkenningMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(_OIDCAuthenticationBackend):
    session_key = ""
    claim_name_field = "identifier_claim_name"

    def authenticate(self, request, *args, **kwargs):
        # Differentiate between DigiD/eHerkenning authentication via OIDC and admin login
        # via OIDC by checking the callback url
        if (
            not self.config.enabled
            or reverse(self.get_settings("OIDC_AUTHENTICATION_CALLBACK_URL"))
            != request.path
        ):
            return None

        return super().authenticate(request, *args, **kwargs)

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
        logger.debug("OIDC claims received: %s", claims)

        if (claim_name := self.get_settings(self.claim_name_field)) not in claims:
            logger.error(
                "`{claim_name}` not in OIDC claims, cannot proceed with authentication".format(
                    claim_name=claim_name
                )
            )
            return False
        return True


class OIDCAuthenticationDigiDBackend(SoloConfigDigiDMixin, OIDCAuthenticationBackend):
    """
    Allows logging in via OIDC with DigiD
    """

    session_key = DIGID_OIDC_AUTH_SESSION_KEY


class OIDCAuthenticationEHerkenningBackend(
    SoloConfigEHerkenningMixin, OIDCAuthenticationBackend
):
    """
    Allows logging in via OIDC with DigiD
    """

    session_key = EHERKENNING_OIDC_AUTH_SESSION_KEY
