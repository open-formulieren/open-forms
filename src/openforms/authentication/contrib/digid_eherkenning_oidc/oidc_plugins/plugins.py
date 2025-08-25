import warnings
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

import structlog
from digid_eherkenning.oidc.schemas import (
    DIGID_MACHTIGEN_OPTIONS_SCHEMA,
    DIGID_OPTIONS_SCHEMA,
    EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA,
    EHERKENNING_OPTIONS_SCHEMA,
)
from flags.state import flag_enabled
from mozilla_django_oidc_db.plugins import (
    AnonymousUserOIDCPluginProtocol,
    BaseOIDCPlugin,
)
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.typing import ClaimPath, JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.contrib.auth_oidc.plugin import OFBaseOIDCPluginProtocol
from openforms.contrib.auth_oidc.typing import (
    ClaimPathDetails,
    ClaimProcessingInstructions,
)
from openforms.contrib.auth_oidc.utils import process_claims
from openforms.contrib.auth_oidc.views import anon_user_callback_view

from .constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)
from .schemas import (
    EIDAS_COMPANY_SCHEMA,
    EIDAS_SCHEMA,
)

logger = structlog.stdlib.get_logger(__name__)


class BaseDigiDeHerkenningPlugin(
    BaseOIDCPlugin, OFBaseOIDCPluginProtocol, AnonymousUserOIDCPluginProtocol
):
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

        We use the payload instead of the user_info to extract the data, because the claims paths
        configured in the OIDCClient options refer to the structure of the payload and not
        that of the user_info.
        """
        assert payload, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(payload, self.get_sensitive_claims())

        logger.debug("oidc_claims_received", claims=obfuscated_claims)

        try:
            # process_claims in strict mode raises ValueError if *required* claims are
            # missing
            processed_claims = process_claims(
                payload,
                self.get_claim_processing_instructions(),
                strict=self.strict_mode(),
            )
        except ValueError as exc:
            logger.error(
                "claim_processing_failure", reason="claims_incomplete", exc_info=exc
            )
            msg = "Claims verification failed"
            # Raise PermissionDenied rather than SuspiciousOperation - this makes it
            # Django stops trying other (OIDC) authentication backends, which fail
            # because the code was already exchanged for an access token.
            # Note that this backend only runs for the DigiD/eHerkenning configs at all,
            # and those aren't particularly compatible with the admin-OIDC flow anyway.
            # See :meth:`_check_candidate_backend` that prevents this backend from being
            # used for admin OIDC.
            raise PermissionDenied(msg)

        request.session[self.identifier] = processed_claims

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user

    def strict_mode(self, request: HttpRequest | None = None) -> bool:
        return bool(flag_enabled("DIGID_EHERKENNING_OIDC_STRICT", request=request))

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return anon_user_callback_view(request)  # pyright: ignore[reportReturnType] # .as_view() returns HttpResponseBase


@register(OIDC_DIGID_IDENTIFIER)
class OIDCDigidPlugin(BaseDigiDeHerkenningPlugin, OFBaseOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return DIGID_OPTIONS_SCHEMA

    def _get_legacy_callback(self) -> str:
        return "digid_oidc:callback"

    def get_sensitive_claims(self) -> list[ClaimPath]:
        config = self.get_config()

        return [config.options["identity_settings"]["bsn_claim_path"]]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "bsn_claim_path"
                    ],
                    "processed_path": ["bsn_claim"],
                }
            ],
            "strict_required_claims": [],
            "optional_claims": [],
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
        }


@register(OIDC_DIGID_MACHTIGEN_IDENTIFIER)
class OIDCDigiDMachtigenPlugin(BaseDigiDeHerkenningPlugin, OFBaseOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return DIGID_MACHTIGEN_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "representee_bsn_claim_path"
                    ],
                    "processed_path": ["representee_bsn_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "authorizee_bsn_claim_path"
                    ],
                    "processed_path": ["authorizee_bsn_claim"],
                },
            ],
            "strict_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "processed_path": ["mandate_service_id_claim"],
                }
            ],
            "optional_claims": [],
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "digid_machtigen_oidc:callback"

    def get_sensitive_claims(self) -> list[ClaimPath]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["representee_bsn_claim_path"],
            config.options["identity_settings"]["authorizee_bsn_claim_path"],
        ]


@register(OIDC_EH_IDENTIFIER)
class OIDCeHerkenningPlugin(BaseDigiDeHerkenningPlugin, OFBaseOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        optional_claims: list[ClaimPathDetails] = []
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            optional_claims.append(
                {
                    "path_in_claim": branch_number_claim_path,
                    "processed_path": ["branch_number_claim"],
                }
            )

        if identifier_type_claim_path := config.options["identity_settings"].get(
            "identifier_type_claim_path"
        ):
            optional_claims.append(
                {
                    "path_in_claim": identifier_type_claim_path,
                    "processed_path": ["identifier_type_claim"],
                }
            )

        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_claim_path"
                    ],
                    "processed_path": ["legal_subject_claim"],
                },
            ],
            "strict_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_claim_path"
                    ],
                    "processed_path": ["acting_subject_claim"],
                }
            ],
            "optional_claims": optional_claims,
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "eherkenning_oidc:callback"

    def get_sensitive_claims(self) -> list[ClaimPath]:
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
    BaseDigiDeHerkenningPlugin, OFBaseOIDCPluginProtocol
):
    def get_schema(self) -> JSONObject:
        return EHERKENNING_BEWINDVOERING_OPTIONS_SCHEMA

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        optional_claims: list[ClaimPathDetails] = []
        if branch_number_claim_path := config.options["identity_settings"].get(
            "branch_number_claim_path"
        ):
            optional_claims.append(
                {
                    "path_in_claim": branch_number_claim_path,
                    "processed_path": ["branch_number_claim"],
                }
            )

        if identifier_type_claim_path := config.options["identity_settings"].get(
            "identifier_type_claim_path"
        ):
            optional_claims.append(
                {
                    "path_in_claim": identifier_type_claim_path,
                    "processed_path": ["identifier_type_claim"],
                }
            )

        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_claim_path"
                    ],
                    "processed_path": ["legal_subject_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "representee_claim_path"
                    ],
                    "processed_path": ["representee_claim"],
                },
            ],
            "strict_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_claim_path"
                    ],
                    "processed_path": ["acting_subject_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "processed_path": ["mandate_service_id_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "mandate_service_uuid_claim_path"
                    ],
                    "processed_path": ["mandate_service_uuid_claim"],
                },
            ],
            "optional_claims": optional_claims,
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
        }

    def _get_legacy_callback(self) -> str:
        return "eherkenning_bewindvoering_oidc:callback"

    def get_sensitive_claims(self) -> list[ClaimPath]:
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

    def get_sensitive_claims(self) -> list[ClaimPath]:
        config = self.get_config()

        return [
            config.options["identity_settings"][
                "legal_subject_bsn_identifier_claim_path"
            ],
            config.options["identity_settings"][
                "legal_subject_pseudo_identifier_claim_path"
            ],
            config.options["identity_settings"]["legal_subject_first_name_claim_path"],
            config.options["identity_settings"]["legal_subject_family_name_claim_path"],
        ]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        # We expect one of `legal_subject_bsn_identifier_claim_path` or
        # `legal_subject_pseudo_identifier_claim_path` is provided. But because of the
        # "one or the other" relation, we mark them both as optional, and use
        # ``one_of_required_claims`` as a final validation step.
        # TODO: are these always required??
        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_first_name_claim_path"
                    ],
                    "processed_path": ["legal_subject_first_name_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_family_name_claim_path"
                    ],
                    "processed_path": ["legal_subject_family_name_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_date_of_birth_claim_path"
                    ],
                    "processed_path": ["legal_subject_date_of_birth_claim"],
                },
            ],
            "strict_required_claims": [],
            "optional_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_bsn_identifier_claim_path"
                    ],
                    "processed_path": ["legal_subject_bsn_identifier_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_pseudo_identifier_claim_path"
                    ],
                    "processed_path": ["legal_subject_pseudo_identifier_claim"],
                },
            ],
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
            "one_of_required_claims": (
                ["legal_subject_bsn_identifier_claim"],
                ["legal_subject_pseudo_identifier_claim"],
            ),
        }


@register(OIDC_EIDAS_COMPANY_IDENTIFIER)
class OIDCEidasCompanyPlugin(BaseDigiDeHerkenningPlugin):
    def get_schema(self) -> JSONObject:
        return EIDAS_COMPANY_SCHEMA

    def get_sensitive_claims(self) -> list[ClaimPath]:
        config = self.get_config()

        return [
            config.options["identity_settings"]["legal_subject_identifier_claim_path"],
            config.options["identity_settings"][
                "acting_subject_bsn_identifier_claim_path"
            ],
            config.options["identity_settings"][
                "acting_subject_pseudo_identifier_claim_path"
            ],
            config.options["identity_settings"]["acting_subject_first_name_claim_path"],
            config.options["identity_settings"][
                "acting_subject_family_name_claim_path"
            ],
        ]

    def get_claim_processing_instructions(self) -> ClaimProcessingInstructions:
        config = self.get_config()

        # We expect one of `acting_subject_bsn_identifier_claim_path` or
        # `acting_subject_pseudo_identifier_claim_path` is provided. But because of the
        # "one or the other" relation, we mark them both as optional, and use
        # ``one_of_required_claims`` as a final validation step.
        # TODO: are these always required??
        return {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_name_claim_path"
                    ],
                    "processed_path": ["legal_subject_name_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "legal_subject_identifier_claim_path"
                    ],
                    "processed_path": ["legal_subject_identifier_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_first_name_claim_path"
                    ],
                    "processed_path": ["acting_subject_first_name_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_family_name_claim_path"
                    ],
                    "processed_path": ["acting_subject_family_name_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_date_of_birth_claim_path"
                    ],
                    "processed_path": ["acting_subject_date_of_birth_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "mandate_service_id_claim_path"
                    ],
                    "processed_path": ["mandate_service_id_claim"],
                },
            ],
            "strict_required_claims": [],
            "optional_claims": [
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_bsn_identifier_claim_path"
                    ],
                    "processed_path": ["acting_subject_bsn_identifier_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "acting_subject_pseudo_identifier_claim_path"
                    ],
                    "processed_path": ["acting_subject_pseudo_identifier_claim"],
                },
            ],
            "loa_claims": {
                "path_in_claim": config.options["loa_settings"]["claim_path"],
                "default": config.options["loa_settings"]["default"],
                "value_mapping": config.options["loa_settings"]["value_mapping"],
                "processed_path": ["loa_claim"],
            },
            "one_of_required_claims": (
                ["acting_subject_bsn_identifier_claim"],
                ["acting_subject_pseudo_identifier_claim"],
            ),
        }
