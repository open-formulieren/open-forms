from itertools import chain

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import resolve

import structlog
from furl import furl
from glom import Path, glom
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.plugins import (
    AnonymousUserOIDCPluginProtocol,
    BaseOIDCPlugin,
)
from mozilla_django_oidc_db.registry import register
from mozilla_django_oidc_db.typing import JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
)

from openforms.forms.models.form import Form
from openforms.forms.models.form_authentication_backend import FormAuthenticationBackend

from .....contrib.auth_oidc.views import anon_user_callback_view
from ...digid_eherkenning_oidc.oidc_plugins.types import (
    ClaimProcessingInstructions,
)
from ...digid_eherkenning_oidc.oidc_plugins.utils import (
    get_of_auth_plugin,
    process_claims,
)
from ..models import AttributeGroup
from .constants import OIDC_YIVI_IDENTIFIER

logger = structlog.stdlib.get_logger(__name__)


@register(OIDC_YIVI_IDENTIFIER)
class YiviPlugin(BaseOIDCPlugin, AnonymousUserOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return

    def verify_claims(self, claims: JSONObject) -> bool:
        # Not used
        return False

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
        assert payload, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(payload, self.get_sensitive_claims())

        log = logger.bind(claims=obfuscated_claims)
        log.debug("received_oidc_claims")

        try:
            # Here we use the payload instead of the user_info, because the claims
            # configured in the OIDCClient options refer to the structure of the payload and not
            # that of the user_info.
            processed_claims = self.process_claims(request, payload)
        except ValueError as exc:
            log.error(
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

    def _process_claims(self, request: HttpRequest, claims: JSONObject) -> JSONObject:
        config = self.get_config()

        return process_claims(
            claims,
            config,
            self.get_claim_processing_instructions(request, claims, config),
            # Yivi cannot be strict, as all its attributes should be optional!
            strict=False,
            legacy=True,
        )

    def process_claims(self, request: HttpRequest, claims: JSONObject) -> JSONObject:
        processed_claims = self._process_claims(request, claims)

        processed_claims["additional_claims"] = self.extract_additional_claims(
            request, claims
        )
        return processed_claims

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return anon_user_callback_view(request)

    def extract_additional_claims(
        self, request: HttpRequest, claims: JSONObject
    ) -> JSONObject:
        return_url = request.session.get(_RETURN_URL_SESSION_KEY, "")
        return_path = furl(return_url).path
        _, _, kwargs = resolve(str(return_path))

        plugin = get_of_auth_plugin(self.get_config())

        try:
            form = Form.objects.get(slug=kwargs.get("slug"))

            auth_backend = FormAuthenticationBackend.objects.get(
                form=form, backend=plugin.identifier
            )
        except (Form.DoesNotExist, FormAuthenticationBackend.DoesNotExist):
            return {}

        attributes_to_add = AttributeGroup.objects.filter(
            name__in=(auth_backend.options or {}).get(
                "additional_attributes_groups", []
            )
        ).values_list("attributes", flat=True)

        return {
            attribute: claims[attribute]
            for attribute in list(chain.from_iterable(attributes_to_add))
            if attribute in claims
        }

    def get_claim_processing_instructions(
        self, request: HttpRequest, claims: JSONObject, config: OIDCClient
    ) -> ClaimProcessingInstructions:
        bsn_claim_path = config.options["identity_settings"]["bsn_claim_path"]
        kvk_claim_path = config.options["identity_settings"]["kvk_claim_path"]

        has_bsn_claim = bool(glom(claims, Path(*bsn_claim_path), default=False))
        has_kvk_claim = bool(glom(claims, Path(*kvk_claim_path), default=False))

        claim_processing_instruction: ClaimProcessingInstructions = {
            "always_required_claims": [],
            "optional_claims": [],
            "strict_required_claims": [],
            "loa_claims": {"default": "", "claim_path": [], "value_mapping": []},
        }

        match (has_bsn_claim, has_kvk_claim):
            case True, _:
                claim_processing_instruction["loa_claims"] = {
                    "default": config.options["identity_settings"]["bsn_default_loa"],
                    "claim_path": config.options["identity_settings"][
                        "bsn_loa_claim_path"
                    ],
                    "value_mapping": config.options["identity_settings"][
                        "bsn_loa_value_mapping"
                    ],
                }
            case False, True:
                claim_processing_instruction["loa_claims"] = {
                    "default": config.options["identity_settings"]["kvk_default_loa"],
                    "claim_path": config.options["identity_settings"][
                        "kvk_loa_claim_path"
                    ],
                    "value_mapping": config.options["identity_settings"][
                        "kvk_loa_value_mapping"
                    ],
                }
            case False, False:
                pass

        return claim_processing_instruction
