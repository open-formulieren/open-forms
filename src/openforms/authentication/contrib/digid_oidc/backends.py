import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse

from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from openforms.authentication.constants import AuthAttribute

from .mixins import SoloConfigMixin
from .models import OpenIDConnectPublicConfig
from .settings import OIDC_AUTHENTICATION_CALLBACK_URL

logger = logging.getLogger(__name__)


class OIDCAuthenticationDigiDBackend(SoloConfigMixin, _OIDCAuthenticationBackend):
    """
    Allows logging in via OIDC with DigiD
    """

    def __init__(self, *args, **kwargs):
        self.config = OpenIDConnectPublicConfig.get_solo()

        if not self.config.enabled:
            return

        super().__init__(*args, **kwargs)

    def authenticate(self, request, *args, **kwargs):
        # Differentiate between DigiD authentication via OIDC and admin login
        # via OIDC by checking the callback url
        if (
            not self.config.enabled
            or reverse(OIDC_AUTHENTICATION_CALLBACK_URL) != request.path
        ):
            return None

        return super().authenticate(request, *args, **kwargs)

    def get_or_create_user(self, access_token, id_token, payload):
        user_info = self.get_userinfo(access_token, id_token, payload)
        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        self.request.session[AuthAttribute.bsn] = payload[
            self.get_settings("bsn_claim_name")
        ]
        user = AnonymousUser()
        user.is_active = True
        return user

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""
        logger.debug("OIDC claims received: %s", claims)

        if self.get_settings("bsn_claim_name") not in claims:
            logger.error("`bsn` not in OIDC claims, cannot proceed with authentication")
            return False
        return True
