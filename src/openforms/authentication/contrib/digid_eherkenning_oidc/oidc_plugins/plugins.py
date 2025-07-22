import warnings
from typing import Any, Protocol

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

import structlog
from flags.state import flag_enabled
from mozilla_django_oidc_db.plugins import (
    AnonymousUserOIDCPluginProtocol,
    BaseOIDCPlugin,
)
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.typing import JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims
from typing_extensions import deprecated

from .....contrib.auth_oidc.views import anon_user_callback_view
from .constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)
from .schemas import (
    DIGID_MACHTIGEN_OPTIONS_SCHEMA,
    DIGID_OPTIONS_SCHEMA,
    EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA,
    EHERKENNING_OPTIONS_SCHEMA,
    EIDAS_COMPANY_SCHEMA,
    EIDAS_SCHEMA,
)
from .types import ClaimPathWithLegacy, ClaimProcessingInstructions
from .utils import process_claims

logger = structlog.stdlib.get_logger(__name__)


class OFLegacyOIDCPluginProtocol(Protocol):
    @deprecated(
        "These plugin-specific callback URLs are deprecated. "
        "Instead, use the generic callback URL in urls.py - it"
        " can handle the different configs."
    )
    def _get_legacy_callback(self) -> str:
        """Get the django URL name of the callback URL."""
        ...


class BaseDigiDeHerkenningPlugin(BaseOIDCPlugin, AnonymousUserOIDCPluginProtocol):
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

        return super().get_setting(attr, *args)

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
        request: HttpRequest,
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

        processed_claims = self._process_claims(payload)
        request.session[self.identifier] = processed_claims

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user

    def _process_claims(self, claims: JSONObject) -> JSONObject:
        config = self.get_config()

        return process_claims(
            claims,
            config,
            self.get_claim_processing_instructions(),
            self.strict_mode(),
            legacy=True,
        )

    def strict_mode(self, request: HttpRequest | None = None) -> bool:
        return bool(flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request))

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return anon_user_callback_view(request)


@register(OIDC_DIGID_IDENTIFIER)
class OIDCDigidPlugin(BaseDigiDeHerkenningPlugin, OFLegacyOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA

    def _get_legacy_callback(self) -> str:
        return "digid_oidc:callback"

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [config.options["identity_settings"]["bsn_claim_path"]]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"]["bsn_claim_path"],
                    "legacy": "bsn_claim",
                }
            ],
            "strict_required_claims": [],
            "optional_claims": [],
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }


@register(OIDC_DIGID_MACHTIGEN_IDENTIFIER)
class OIDCDigiDMachtigenPlugin(BaseDigiDeHerkenningPlugin, OFLegacyOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return DIGID_MACHTIGEN_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "representee_bsn_claim_path"
                    ],
                    "legacy": "representee_bsn_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "authorizee_bsn_claim_path"
                    ],
                    "legacy": "authorizee_bsn_claim",
                },
            ],
            "strict_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "legacy": "mandate_service_id_claim",
                }
            ],
            "optional_claims": [],
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "digid_machtigen_oidc:callback"

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["representee_bsn_claim_path"],
            config.options["identity_settings"]["authorizee_bsn_claim_path"],
        ]


@register(OIDC_EH_IDENTIFIER)
class OIDCeHerkenningPlugin(BaseDigiDeHerkenningPlugin, OFLegacyOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        optional_claims: list[ClaimPathWithLegacy] = []
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            optional_claims.append(
                {"path": branch_number_claim_path, "legacy": "branch_number_claim"}
            )

        if identifier_type_claim_path := config.options["identity_settings"].get(
            "identifier_type_claim_path"
        ):
            optional_claims.append(
                {"path": identifier_type_claim_path, "legacy": "identifier_type_claim"}
            )

        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_claim_path"
                    ],
                    "legacy": "legal_subject_claim",
                },
            ],
            "strict_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_claim_path"
                    ],
                    "legacy": "acting_subject_claim",
                }
            ],
            "optional_claims": optional_claims,
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "eherkenning_oidc:callback"

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        sensitive_claims = [
            config.options["identity_settings"]["legal_subject_claim_path"]
        ]
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            sensitive_claims.append(branch_number_claim_path)

        return sensitive_claims


@register(OIDC_EH_BEWINDVOERING_IDENTIFIER)
class OIDCeHerkenningBewindvoeringPlugin(
    BaseDigiDeHerkenningPlugin, OFLegacyOIDCPluginProtocol
):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        optional_claims: list[ClaimPathWithLegacy] = []
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            optional_claims.append(
                {"path": branch_number_claim_path, "legacy": "branch_number_claim"}
            )

        if identifier_type_claim_path := config.options["identity_settings"].get(
            "identifier_type_claim_path"
        ):
            optional_claims.append(
                {"path": identifier_type_claim_path, "legacy": "identifier_type_claim"}
            )

        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_claim_path"
                    ],
                    "legacy": "legal_subject_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "representee_claim_path"
                    ],
                    "legacy": "representee_claim",
                },
            ],
            "strict_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_claim_path"
                    ],
                    "legacy": "acting_subject_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "legacy": "mandate_service_id_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "mandate_service_uuid_claim_path"
                    ],
                    "legacy": "mandate_service_uuid_claim",
                },
            ],
            "optional_claims": optional_claims,
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "eherkenning_bewindvoering_oidc:callback"

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        sensitive_claims = [
            config.options["identity_settings"]["legal_subject_claim_path"],
            config.options["identity_settings"]["representee_claim_path"],
        ]
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            sensitive_claims.append(branch_number_claim_path)

        return sensitive_claims


@register(OIDC_EIDAS_IDENTIFIER)
class OIDCEidasPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return EIDAS_SCHEMA

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["legal_subject_identifier_claim_path"],
            config.options["identity_settings"]["legal_subject_first_name_claim_path"],
            config.options["identity_settings"]["legal_subject_family_name_claim_path"],
        ]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        # TODO: are these always required??
        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_identifier_claim_path"
                    ],
                    "legacy": "legal_subject_identifier_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_first_name_claim_path"
                    ],
                    "legacy": "legal_subject_first_name_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_family_name_claim_path"
                    ],
                    "legacy": "legal_subject_family_name_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_date_of_birth_claim_path"
                    ],
                    "legacy": "legal_subject_date_of_birth_claim",
                },
            ],
            "strict_required_claims": [],
            "optional_claims": [
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_identifier_type_claim_path"
                    ],
                    "legacy": "legal_subject_identifier_type_claim",
                },
            ],
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }


@register(OIDC_EIDAS_COMPANY_IDENTIFIER)
class OIDCEidasCompanyPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return EIDAS_COMPANY_SCHEMA

    def get_sensitive_claims(self) -> list[list[str]]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["legal_subject_identifier_claim_path"],
            config.options["identity_settings"]["acting_subject_identifier_claim_path"],
            config.options["identity_settings"]["acting_subject_first_name_claim_path"],
            config.options["identity_settings"][
                "acting_subject_family_name_claim_path"
            ],
        ]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        # TODO: are these always required??
        return {
            "always_required_claims": [
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_name_claim_path"
                    ],
                    "legacy": "legal_subject_name_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "legal_subject_identifier_claim_path"
                    ],
                    "legacy": "legal_subject_identifier_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_identifier_claim_path"
                    ],
                    "legacy": "acting_subject_identifier_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_first_name_claim_path"
                    ],
                    "legacy": "acting_subject_first_name_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_family_name_claim_path"
                    ],
                    "legacy": "acting_subject_family_name_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_date_of_birth_claim_path"
                    ],
                    "legacy": "acting_subject_date_of_birth_claim",
                },
                {
                    "path": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "legacy": "mandate_service_id_claim",
                },
            ],
            "strict_required_claims": [],
            "optional_claims": [
                {
                    "path": config.options["identity_settings"][
                        "acting_subject_identifier_type_claim_path"
                    ],
                    "legacy": "acting_subject_identifier_type_claim",
                },
            ],
            "loa_claims": {
                "claim_path": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
            },
        }
