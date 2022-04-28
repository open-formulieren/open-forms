import logging

from digid_eherkenning_oidc_generics.backends import OIDCAuthenticationBackend
from digid_eherkenning_oidc_generics.mixins import (
    MachtigenBackendMixin,
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    SoloConfigEHerkenningMixin,
)

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
    MachtigenBackendMixin, SoloConfigDigiDMachtigenMixin, OIDCAuthenticationBackend
):
    session_key = DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY

    @property
    def claim_names(self):
        return [
            self.config.vertegenwoordigde_claim_name,
            self.config.gemachtigde_claim_name,
        ]


class OIDCAuthenticationEHerkenningBewindvoeringBackend(
    MachtigenBackendMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    OIDCAuthenticationBackend,
):
    session_key = EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY

    @property
    def claim_names(self):
        return [
            self.config.vertegenwoordigde_company_claim_name,
            self.config.gemachtigde_person_claim_name,
        ]
