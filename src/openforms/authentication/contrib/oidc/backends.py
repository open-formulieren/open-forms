import logging

from oidc_generics.backends import OIDCAuthenticationBackend
from oidc_generics.mixins import (
    MultipleClaimMixin,
    SoloConfigAzureADMixin,
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningBewindvoeringMixin,
    SoloConfigEHerkenningMixin,
)

from .constants import (
    AZURE_AD_OIDC_AUTH_SESSION_KEY,
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
    MultipleClaimMixin, SoloConfigDigiDMachtigenMixin, OIDCAuthenticationBackend
):
    session_key = DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY

    @property
    def claim_names(self):
        return [
            self.config.vertegenwoordigde_claim_name,
            self.config.gemachtigde_claim_name,
        ]


class OIDCAuthenticationEHerkenningBewindvoeringBackend(
    MultipleClaimMixin,
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


class OIDCAuthenticationAzureADBackend(
    SoloConfigAzureADMixin,
    OIDCAuthenticationBackend,
):
    session_key = AZURE_AD_OIDC_AUTH_SESSION_KEY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self.config, self.config_identifier_field, self.config.username_claim)
