import logging
from typing import override

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from digid_eherkenning.oidc.claims import process_claims
from digid_eherkenning.oidc.models import BaseConfig
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.typing import JSONObject

from .plugin import YiviOpenIDConnectConfig, YiviOIDCAuthentication

logger = logging.getLogger(__name__)


class YiviOIDCBackend(OIDCAuthenticationBackend):
    """
    A backend specialised to the yivi subclassed model.
    """

    @override
    def _check_candidate_backend(self) -> bool:
        # if we're dealing with a mozilla-django-oidc-db config that is *not* a
        # yivi subclass, then don't bother.
        if not issubclass(self.config_class, BaseConfig):
            return False
        return super()._check_candidate_backend()

    def get_or_create_user(
        self, access_token: str, id_token: str, payload: JSONObject
    ) -> AnonymousUser:
        """
        Return a "fake" Django user.

        If the claims are valid, we only process them and do not create or update an
        actual Django user.
        """
        assert isinstance(self.request, HttpRequest)

        user_info = self.get_userinfo(access_token, id_token, payload)
        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = "Claims verification failed"
            # Raise PermissionDenied rather than SuspiciousOperation - this makes it
            # Django stops trying other (OIDC) authentication backends, which fail
            # because the code was already exchanged for an access token.
            # Note that this backend only runs for the Yivi configs at all, and it isn't
            # particularly compatible with the admin-OIDC flow anyway.
            # See :meth:`_check_candidate_backend` that prevents this backend from being
            # used for admin OIDC.
            raise PermissionDenied(msg)

        self._extract_and_store_claims(payload)

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user

    def _process_claims(self, claims: JSONObject) -> JSONObject:
        # see if we can use a cached config instance from the settings configuration
        assert hasattr(self, "_config") and isinstance(self._config, BaseConfig)
        return process_claims(claims, self._config, strict=False)

    @override
    def verify_claims(self, claims) -> bool:
        """Verify the provided claims to decide if authentication should be allowed."""
        assert claims, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(claims, self.OIDCDB_SENSITIVE_CLAIMS)
        logger.debug("OIDC claims received: %s", obfuscated_claims)

        # process_claims in strict mode raises ValueError if *required* claims are
        # missing
        try:
            processed_claims = self._process_claims(claims)
        except ValueError as exc:
            logger.error(
                "Claims are incomplete",
                exc_info=exc,
                extra={"claims": obfuscated_claims},
            )
            return False

        return True

    def _extract_and_store_claims(self, claims: JSONObject) -> None:
        """
        Extract the claims configured on the config and store them in the session.
        """
        assert self.config_class and self.config_class is YiviOpenIDConnectConfig
        session_key = YiviOIDCAuthentication().session_key
        procssed_claims = self._process_claims(claims)
        assert self.request
        self.request.session[session_key] = procssed_claims
