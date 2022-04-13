import logging
from copy import deepcopy

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import SuspiciousOperation

from glom import PathAccessError, glom

from digid_eherkenning_oidc_generics.backends import OIDCAuthenticationBackend
from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    SoloConfigEHerkenningMixin,
)
from digid_eherkenning_oidc_generics.utils import obfuscate_claim

from .constants import (
    DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY,
    DIGID_OIDC_AUTH_SESSION_KEY,
    EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY,
    EHERKENNING_OIDC_AUTH_SESSION_KEY,
)

logger = logging.getLogger(__name__)


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


class OIDCAuthenticationDigiDMachtigenBackend(
    SoloConfigDigiDMachtigenMixin, OIDCAuthenticationBackend
):
    session_key = DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY

    def get_or_create_user(self, access_token, id_token, payload):
        claims_verified = self.verify_claims(payload)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        self.extract_claims(payload)

        user = AnonymousUser()
        user.is_active = True
        return user

    def extract_claims(self, payload: dict) -> None:
        claim_names = [
            self.config.vertegenwoordigde_claim_name,
            self.config.gemachtigde_claim_name,
        ]

        self.request.session[self.session_key] = {}
        for claim_name in claim_names:
            self.request.session[self.session_key][claim_name] = glom(
                payload, claim_name
            )

    def log_received_claims(self, claims: dict):
        copied_claims = deepcopy(claims)

        def _obfuscate_claims_values(claims_to_obfuscate: dict) -> dict:
            for key, value in claims_to_obfuscate.items():
                if isinstance(value, dict):
                    _obfuscate_claims_values(value)
                else:
                    claims_to_obfuscate[key] = obfuscate_claim(value)
            return claims_to_obfuscate

        obfuscated_claims = _obfuscate_claims_values(copied_claims)
        logger.debug("OIDC claims received: %s", obfuscated_claims)

    def verify_claims(self, claims: dict) -> bool:
        expected_claim_names = [
            self.config.vertegenwoordigde_claim_name,
            self.config.gemachtigde_claim_name,
        ]

        self.log_received_claims(claims)

        for expected_claim in expected_claim_names:
            try:
                glom(claims, expected_claim)
            except PathAccessError:
                logger.error(
                    "`%s` not in OIDC claims, cannot proceed with DigiD Machtigen authentication",
                    expected_claim,
                )
                return False

        return True


class OIDCAuthenticationEHerkenningBewindvoeringBackend(
    SoloConfigEHerkenningBewindvoeringMixin, OIDCAuthenticationBackend
):
    session_key = EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY

    def get_or_create_user(self, access_token, id_token, payload):
        claims_verified = self.verify_claims(payload)
        if not claims_verified:
            msg = "Claims verification failed"
            raise SuspiciousOperation(msg)

        self.extract_claims(payload)

        user = AnonymousUser()
        user.is_active = True
        return user

    @property
    def claim_names(self):
        return [
            self.config.vertegenwoordigde_company_claim_name,
            self.config.vertegenwoordigde_person_claim_name,
            self.config.gemachtigde_person_claim_name,
        ]

    def extract_claims(self, payload: dict) -> None:
        self.request.session[self.session_key] = {}
        for claim_name in self.claim_names:
            self.request.session[self.session_key][claim_name] = glom(
                payload, claim_name
            )

    def log_received_claims(self, claims: dict):
        copied_claims = deepcopy(claims)

        def _obfuscate_claims_values(claims_to_obfuscate: dict) -> dict:
            for key, value in claims_to_obfuscate.items():
                if isinstance(value, dict):
                    _obfuscate_claims_values(value)
                else:
                    claims_to_obfuscate[key] = obfuscate_claim(value)
            return claims_to_obfuscate

        obfuscated_claims = _obfuscate_claims_values(copied_claims)
        logger.debug("OIDC claims received: %s", obfuscated_claims)

    def verify_claims(self, claims: dict) -> bool:
        self.log_received_claims(claims)

        for expected_claim in self.claim_names:
            try:
                glom(claims, expected_claim)
            except PathAccessError:
                logger.error(
                    "`%s` not in OIDC claims, cannot proceed with eHerkenning bewindvoering authentication",
                    expected_claim,
                )
                return False

        return True
