import base64
import json
from collections.abc import Collection
from copy import deepcopy
from typing import cast

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
from mozilla_django_oidc_db.typing import ClaimPath, JSONObject
from mozilla_django_oidc_db.utils import obfuscate_claims
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
)
from rest_framework.request import Request

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.auth_oidc.typing import ClaimProcessingInstructions
from openforms.contrib.auth_oidc.utils import (
    get_of_auth_plugin,
    process_claims,
)
from openforms.contrib.auth_oidc.views import anon_user_callback_view
from openforms.forms.models.form_authentication_backend import FormAuthenticationBackend

from ..config import YiviOptions, YiviOptionsSerializer
from .constants import OIDC_YIVI_IDENTIFIER
from .schemas import YIVI_SCHEMA

logger = structlog.stdlib.get_logger(__name__)

type YiviAttributes = Collection[str]
"""
A set of Yivi attribute names.

Either the entire set or none of the set are granted, this cannot be broken up further.
"""

type YiviAttributeGroups = Collection[YiviAttributes]
"""
A collection of Yivi attributes.

Each member can be granted or declined.
"""

type CondisconItem = Collection[YiviAttributes]
"""
A single condiscon item contains possible sets of Yivi attributes.

Note that including an empty attribute sets makes the item optional.
"""


@register(OIDC_YIVI_IDENTIFIER)
class YiviPlugin(BaseOIDCPlugin, AnonymousUserOIDCPluginProtocol):
    def get_schema(self) -> JSONObject:
        return YIVI_SCHEMA

    def get_sensitive_claims(
        self,
        additional_attributes: YiviAttributeGroups,
    ) -> Collection[ClaimPath]:
        config = self.get_config()

        sensitive_claims: list[ClaimPath] = [
            config.options["identity_settings"]["bsn_claim_path"],
            config.options["identity_settings"]["kvk_claim_path"],
            config.options["identity_settings"]["pseudo_claim_path"],
            # All claims that we receive, that were part of the Yivi additional attributes,
            # should be marked as sensitive.
            *(
                [attribute]
                for attribute_group in additional_attributes
                for attribute in attribute_group
            ),
        ]
        return sensitive_claims

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

        additional_attributes = self.get_additional_attributes(request)

        obfuscated_claims = obfuscate_claims(
            payload, self.get_sensitive_claims(additional_attributes)
        )

        logger.debug("oidc_claims_received", claims=obfuscated_claims)

        try:
            # Here we use the payload instead of the user_info, because the claims
            # configured in the OIDCClient options refer to the structure of the payload and not
            # that of the user_info.
            processed_claims = self.process_claims(payload, additional_attributes)
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

    def process_claims(
        self, claims: JSONObject, additional_attributes: YiviAttributeGroups
    ) -> JSONObject:
        config = self.get_config()

        processed_claims = process_claims(
            claims,
            self.get_claim_processing_instructions(
                claims, config, additional_attributes
            ),
            # Yivi cannot be strict, as all its attributes should be optional!
            strict=False,
        )
        return processed_claims

    def validate_settings(self) -> None:
        pass

    def handle_callback(self, request: HttpRequest) -> HttpResponse:
        return anon_user_callback_view(request)  # pyright: ignore[reportReturnType] # .as_view() returns HttpResponseBase

    def _get_auth_backend_options(self, form_slug: str) -> YiviOptions | None:
        plugin = get_of_auth_plugin(self)

        auth_backend = FormAuthenticationBackend.objects.filter(
            form__slug=form_slug, backend=plugin.identifier
        ).first()
        if auth_backend is None:
            return None

        serializer = YiviOptionsSerializer(data=auth_backend.options)
        # TODO: this should be picked up in the digest email, but unfortunately time
        # constraints postpone it
        if not serializer.is_valid():
            logger.error(
                "invalid_yivi_configuration_detected",
                form_slug=form_slug,
                errors=serializer.errors,
            )
            raise RuntimeError("Invalid Yivi configuration options detected")

        return serializer.validated_data

    def get_additional_attributes(self, request: HttpRequest) -> YiviAttributeGroups:
        return_url = request.session.get(_RETURN_URL_SESSION_KEY, "")
        return_path = furl(return_url).path
        _, _, kwargs = resolve(str(return_path))

        auth_backend_options = self._get_auth_backend_options(kwargs.get("slug"))
        if auth_backend_options is None:
            return []

        return [
            cast(list[str], attributes_group.attributes)
            for attributes_group in auth_backend_options["additional_attributes_groups"]
        ]

    def get_claim_processing_instructions(
        self,
        claims: JSONObject,
        config: OIDCClient,
        additional_attributes: YiviAttributeGroups,
    ) -> ClaimProcessingInstructions:
        bsn_claim_path = config.options["identity_settings"]["bsn_claim_path"]
        kvk_claim_path = config.options["identity_settings"]["kvk_claim_path"]

        has_bsn_claim = bool(glom(claims, Path(*bsn_claim_path), default=False))
        has_kvk_claim = bool(glom(claims, Path(*kvk_claim_path), default=False))

        claim_processing_instruction: ClaimProcessingInstructions = {
            "always_required_claims": [],
            "optional_claims": [
                # The processed paths should match those present in
                # openforms.authentication.contrib.yivi_oidc.plugin.YiviClaims
                {
                    "path_in_claim": config.options["identity_settings"][
                        "bsn_claim_path"
                    ],
                    "processed_path": ["bsn_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "kvk_claim_path"
                    ],
                    "processed_path": ["kvk_claim"],
                },
                {
                    "path_in_claim": config.options["identity_settings"][
                        "pseudo_claim_path"
                    ],
                    "processed_path": ["pseudo_claim"],
                },
            ],
            "strict_required_claims": [],
            "loa_claims": {
                "default": "",
                "path_in_claim": [],
                "value_mapping": [],
                "processed_path": [],
            },
        }

        match (has_bsn_claim, has_kvk_claim):
            case True, _:
                claim_processing_instruction["loa_claims"] = {
                    "default": config.options["loa_settings"]["bsn_default_loa"],
                    "path_in_claim": config.options["loa_settings"][
                        "bsn_loa_claim_path"
                    ],
                    "value_mapping": config.options["loa_settings"][
                        "bsn_loa_value_mapping"
                    ],
                    "processed_path": ["loa_claim"],
                }
            case False, True:
                claim_processing_instruction["loa_claims"] = {
                    "default": config.options["loa_settings"]["kvk_default_loa"],
                    "path_in_claim": config.options["loa_settings"][
                        "kvk_loa_claim_path"
                    ],
                    "value_mapping": config.options["loa_settings"][
                        "kvk_loa_value_mapping"
                    ],
                    "processed_path": ["loa_claim"],
                }
            case False, False:
                pass

        # Additional Yivi attributes
        claim_processing_instruction["optional_claims"].extend(
            [
                {
                    "path_in_claim": [attribute],
                    "processed_path": ["additional_claims", attribute],
                }
                for attribute_group in additional_attributes
                for attribute in attribute_group
                if attribute in claims
            ]
        )
        return claim_processing_instruction

    def _build_authentication_condiscon(self, options: YiviOptions) -> CondisconItem:
        """
        Create the "authentication attributes" part of the Signicat Yivi condiscon.
        """
        yivi_config = self.get_config()

        if not len(options["authentication_options"]):
            # If no authentication options are selected, fallback to the pseudo_claim
            return [glom(yivi_config.options, "identity_settings.pseudo_claim_path")]

        authentication_condiscon: CondisconItem = []
        for option in options["authentication_options"]:
            match option:
                case AuthAttribute.bsn:
                    bsn_attributes: ClaimPath = deepcopy(
                        glom(yivi_config.options, "identity_settings.bsn_claim_path")
                    )

                    if bsn_loa_claim_path := glom(
                        yivi_config.options, "loa_settings.bsn_loa_claim_path"
                    ):
                        bsn_attributes += bsn_loa_claim_path

                    authentication_condiscon.append(bsn_attributes)

                case AuthAttribute.kvk:
                    kvk_attributes: ClaimPath = deepcopy(
                        glom(yivi_config.options, "identity_settings.kvk_claim_path")
                    )

                    if kvk_loa_claim_path := glom(
                        yivi_config.options, "loa_settings.kvk_loa_claim_path"
                    ):
                        kvk_attributes += kvk_loa_claim_path

                    authentication_condiscon.append(kvk_attributes)

                case AuthAttribute.pseudo:
                    pseudo_attributes: ClaimPath = deepcopy(
                        glom(
                            yivi_config.options,
                            "identity_settings.pseudo_claim_path",
                        )
                    )
                    authentication_condiscon.append(pseudo_attributes)

        return authentication_condiscon

    @staticmethod
    def _build_additional_attributes_condiscon(
        options: YiviOptions,
    ) -> Collection[CondisconItem]:
        """
        Helper function for creating the "additional attributes" part of the Signicat
        Yivi condiscon.

        All the `additional_attributes_groups` are optional, meaning that the end-user
        can choose which information they want to provide. This is defined by the empty
        list in the ``additional_attributes_condiscon`` (see below).

        See https://irma.app/docs/condiscon/#other-features
        """
        additional_attributes_condiscon: Collection[CondisconItem] = [
            [
                cast(YiviAttributes, attributes_group.attributes),
                # The empty list ensures that this attribute becomes optional.
                # This needs to be placed as last, otherwise it doesn't work
                # (see https://dashboard.signicat.com/contact-us/tickets/207907)
                [],
            ]
            for attributes_group in options["additional_attributes_groups"]
        ]

        return additional_attributes_condiscon

    def _get_signicat_yivi_condiscon_scope(self, options: YiviOptions) -> str:
        """
        Return the yivi condiscon scope as a Signicat additional parameter.

        To allow end-users to choose which information they want to provide, we need to
        pass the Yivi scopes as condiscon. With condiscons we can create logic like;
        "the user must provide bsn OR kvk information.".

        Signicat has some documentation about how the scope should be shaped:
        https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request.
        Yivi has some documentation about the codiscon format and logic:
        https://irma.app/docs/condiscon/.

        The scopes-to-add are fetched from the plugin options ``authentication_options``
        and ``additional_attributes_groups``.

        When multiple ``authentication_options`` are defined, the user can choose which
        one to use. Otherwise, if only one is defined, then that one becomes required.
        When no ``authentication_options`` are defined we fallback to the pseudo
        authentication option.

        All the `additional_attributes_groups` are optional, meaning that the end-user
        can choose which information they want to provide.
        """

        # Start with condiscon of authentication attributes
        condiscon_items: Collection[CondisconItem] = [
            self._build_authentication_condiscon(options)
        ]

        additional_attributes_condiscon: Collection[CondisconItem] = (
            self._build_additional_attributes_condiscon(options)
        )
        if additional_attributes_condiscon:
            condiscon_items += additional_attributes_condiscon

        # Turn the condiscon list into a string, and base64 encode it
        condiscon_string = json.dumps(condiscon_items)

        # Create a signicat param scope with the base64 condiscon string.
        # https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request
        base64_bytes = base64.b64encode(condiscon_string.encode("ascii"))
        return f"signicat:param:condiscon_base64:{base64_bytes.decode('ascii')}"

    def get_extra_params(
        self, request: HttpRequest, extra_params: dict
    ) -> dict[str, str | bytes]:
        assert isinstance(request, Request)  # stronger guarantee
        configured_scopes = deepcopy(self.get_setting("oidc_rp_scopes_list"))

        return_url = request.query_params.get("next")
        assert isinstance(return_url, str)
        return_path = furl(return_url).path
        _, _, kwargs = resolve(str(return_path))

        auth_backend_options = self._get_auth_backend_options(kwargs.get("slug"))
        if auth_backend_options is None:
            return extra_params

        configured_scopes.append(
            self._get_signicat_yivi_condiscon_scope(auth_backend_options)
        )

        extra_params["scope"] = " ".join(configured_scopes)
        return extra_params
