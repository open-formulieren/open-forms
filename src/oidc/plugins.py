
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

import structlog
from flags.state import flag_enabled
from mozilla_django_oidc_db.plugins import OIDCBasePlugin
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.typing import JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims

from .constants import OIDC_DIGID_IDENTIFIER
from .schemas import (
    DIGID_OPTIONS_SCHEMA,
)
from .types import ClaimProcessingInstructions
from .utils import process_claims

logger = structlog.stdlib.get_logger(__name__)


@register(OIDC_DIGID_IDENTIFIER)
class OIDCDigidPlugin(OIDCBasePlugin):
    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        # TODO should this be part of the schema?
        return [config.options["identity_settings"]["bsn_claim_path"]]
    
    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {"path": config.options["identity_settings"]["bsn_claim_path"], "legacy": "bsn_claim"}
            ],
            "strict_required_claims": [],
        }
    
    def verify_claims(self, claims: JSONObject) -> bool:
        """Verify the provided claims to decide if authentication should be allowed."""

        assert claims, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(claims, self.get_sensitive_claims())

        log = logger.bind(claims=obfuscated_claims)
        log.debug("received_oidc_claims")

        # process_claims in strict mode raises ValueError if *required* claims are
        # missing
        try:
            self._process_claims(claims)
        except ValueError as exc:
            log.error(
                "claim_processing_failure", reason="claims_incomplete", exc_info=exc
            )
            return False

        return True
    
    def get_or_create_user(
        self, 
        access_token: str, 
        id_token: str, 
        payload: JSONObject, 
        request: HttpRequest
    ) -> AnonymousUser:
        """
        Return a "fake" Django user.

        If the claims are valid, we only process them and do not create or update an
        actual Django user.
        """
        # Here we use the payload instead of the user_info, because the claims
        # configured in the OIDCClient options refer to the structure of the payload and not
        # that of the user_info. 
        claims_verified = self.verify_claims(payload)
        if not claims_verified:
            msg = "Claims verification failed"
            # Raise PermissionDenied rather than SuspiciousOperation - this makes it
            # Django stops trying other (OIDC) authentication backends, which fail
            # because the code was already exchanged for an access token.
            # Note that this backend only runs for the DigiD/eHerkenning configs at all,
            # and those aren't particularly compatible with the admin-OIDC flow anyway.
            # See :meth:`_check_candidate_backend` that prevents this backend from being
            # used for admin OIDC.
            raise PermissionDenied(msg)

        procssed_claims = self._process_claims(payload)
        request.session[self.identifier] = procssed_claims

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user
    
    def _process_claims(self, claims: JSONObject) -> JSONObject:
        # see if we can use a cached config instance from the settings configuration
        config = self.get_config()

        strict_mode = flag_enabled("DIGID_EHERKENNING_OIDC_STRICT")
        assert isinstance(strict_mode, bool)
        return process_claims(claims, config, self.get_claim_processing_instructions(), strict_mode)

