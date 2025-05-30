
import warnings
from abc import abstractmethod
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

import structlog
from flags.state import flag_enabled
from mozilla_django_oidc_db.plugins import OIDCAdminPlugin, OIDCBasePlugin
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.schemas import ADMIN_OPTIONS_SCHEMA
from mozilla_django_oidc_db.typing import JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.authentication.contrib.digid.views import (
    DIGID_MESSAGE_PARAMETER,
    LOGIN_CANCELLED,
)
from openforms.authentication.contrib.eherkenning.views import (
    MESSAGE_PARAMETER as EH_MESSAGE_PARAMETER,
)
from openforms.authentication.contrib.org_oidc.views import callback_view

from .constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_ORG_IDENTIFIER,
)
from .schemas import (
    DIGID_MACHTIGEN_OPTIONS_SCHEMA,
    DIGID_OPTIONS_SCHEMA,
    EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA,
    EHERKENNING_OPTIONS_SCHEMA,
)
from .types import ClaimProcessingInstructions, ErrorMessagesMap
from .utils import process_claims
from .views import anon_user_callback_view

logger = structlog.stdlib.get_logger(__name__)


class BaseDigiDeHerkenningPlugin(OIDCBasePlugin):
    @abstractmethod
    def _get_legacy_callback(self) -> str:
        """Get the django URL name of the callback URL."""
        ...

    @abstractmethod
    def get_error_messages(self) -> ErrorMessagesMap:
        """Return the message code and the error description for a failed login."""
        ...

    def get_setting(self, attr: str, *args) -> Any:
        attr_lower = attr.lower()

        if attr_lower == "oidc_authentication_callback_url":
            if settings.USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS:
                warnings.warn(
                    "Legacy DigiD-eHerkenning callback endpoints will be removed in 4.0",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return self._get_legacy_callback()
            return "oidc_authentication_callback"
        
        return super().get_settings(attr, *args)

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
    
    # TODO find a more elegant way of doing this...
    def create_user(self, claims: JSONObject) -> AnonymousUser:
        # This method is not called since we implemented get_or_create_user
        pass

    def update_user(self, user: AnonymousUser, claims: JSONObject) -> AnonymousUser:
        # This method is not called since we implemented get_or_create_user
        pass
    
    def filter_users_by_claims(self, claims: JSONObject):
        # This method is not called since we implemented get_or_create_user
        pass
        
    
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
        config = self.get_config()

        strict_mode = flag_enabled("DIGID_EHERKENNING_OIDC_STRICT")
        assert isinstance(strict_mode, bool)
        return process_claims(claims, config, self.get_claim_processing_instructions(), strict_mode)
    
    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return anon_user_callback_view(request)



@register(OIDC_DIGID_IDENTIFIER)
class OIDCDigidPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA
    
    def _get_legacy_callback(self) -> str:
        return "digid_oidc:callback"
        
    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [config.options["identity_settings"]["bsn_claim_path"]]
    
    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        # TODO: check if this logic is correct:
        # The claims in "always required" come from the models in OpenForms, 
        # while the other ones come from the digid_eherkenning package
        return {
            "always_required_claims": [
                {"path": config.options["identity_settings"]["bsn_claim_path"], "legacy": "bsn_claim"}
            ],
            "strict_required_claims": [],
        }
    
    def get_error_messages(self) -> ErrorMessagesMap:
        return {
            "access_denied": (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)
        }
    

@register(OIDC_DIGID_MACHTIGEN_IDENTIFIER)
class OIDCDigiDMachtigenPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return DIGID_MACHTIGEN_OPTIONS_SCHEMA
    
    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {"path": config.options["identity_settings"]["representee_bsn_claim_path"], "legacy": "representee_bsn_claim"},
                {"path": config.options["identity_settings"]["authorizee_bsn_claim_path"], "legacy": "authorizee_bsn_claim"}
            ],
            "strict_required_claims": [
                {"path": config.options["identity_settings"]["mandate_service_id_claim_path"], "legacy": "mandate_service_id_claim"}
            ],
        }
    
    def _get_legacy_callback(self) -> str:
        return "digid_machtigen_oidc:callback"
    
    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["representee_bsn_claim_path"],
            config.options["identity_settings"]["authorizee_bsn_claim_path"],
        ]
    
    def get_error_messages(self) -> ErrorMessagesMap:
        return {
            "access_denied": (DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED)
        }
    
@register(OIDC_EH_IDENTIFIER)
class OIDCeHerkenningMachtigenPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_OPTIONS_SCHEMA
    
    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {"path": config.options["identity_settings"]["legal_subject_claim_path"], "legacy": "legal_subject_claim"},
            ],
            "strict_required_claims": [
                {"path": config.options["identity_settings"]["acting_subject_claim_path"], "legacy": "acting_subject_claim"}
            ],
        }
    
    def _get_legacy_callback(self) -> str:
        return "eherkenning_oidc:callback"
    
    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["legal_subject_claim_path"],
            config.options["identity_settings"]["branch_number_claim_path"],
        ]
    
    def get_error_messages(self) -> ErrorMessagesMap:
        eh_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier
        }
        return {
            "access_denied": (eh_message_parameter, LOGIN_CANCELLED)
        }
    
@register(OIDC_EH_BEWINDVOERING_IDENTIFIER)
class OIDCeHerkenningBewindvoeringPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA
    
    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {"path": config.options["identity_settings"]["legal_subject_claim_path"], "legacy": "legal_subject_claim"},
                {"path": config.options["identity_settings"]["representee_claim_path"], "legacy": "representee_claim"},
            ],
            "strict_required_claims": [
                {"path": config.options["identity_settings"]["acting_subject_claim_path"], "legacy": "acting_subject_claim"},
                {"path": config.options["identity_settings"]["mandate_service_id_claim_path"], "legacy": "mandate_service_id_claim"},
                {"path": config.options["identity_settings"]["mandate_service_uuid_claim_path"], "legacy": "mandate_service_uuid_claim"}
            ],
        }
    
    def _get_legacy_callback(self) -> str:
        return "eherkenning_bewindvoering_oidc:callback"
    
    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["legal_subject_claim_path"],
            config.options["identity_settings"]["branch_number_claim_path"],
            config.options["identity_settings"]["representee_claim_path"],
        ]
    
    def get_error_messages(self) -> ErrorMessagesMap:
        eh_message_parameter = EH_MESSAGE_PARAMETER % {
            "plugin_id": self.identifier
        }
        return {
            "access_denied": (eh_message_parameter, LOGIN_CANCELLED)
        }
    
@register(OIDC_ORG_IDENTIFIER)
class OIDCOrgPlugin(OIDCAdminPlugin):
    def get_schema(self) -> JSONObject:
        return ADMIN_OPTIONS_SCHEMA
    
    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return callback_view(request)
    
    def _get_legacy_callback(self) -> str:
        return "org-oidc-callback"