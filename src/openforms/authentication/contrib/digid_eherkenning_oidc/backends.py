import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from digid_eherkenning.oidc.models import OpenIDConnectBaseConfig
from glom import Path, PathAccessError, glom
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.config import dynamic_setting
from mozilla_django_oidc_db.typing import ClaimPath
from mozilla_django_oidc_db.utils import obfuscate_claims
from typing_extensions import override

from openforms.typing import JSONObject

from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
)
from .plugin import get_config_to_plugin

logger = logging.getLogger(__name__)


class DigiDEHerkenningOIDCBackend(OIDCAuthenticationBackend):
    """
    A backend specialised to the digid-eherkenning-generics subclassed model.
    """

    MANDATE_CLAIMS = dynamic_setting[dict[str, ClaimPath]]()
    """
    Mapping of destination key and the claim paths to extract.
    """

    @override
    def _check_candidate_backend(self) -> bool:
        # if we're dealing with a mozilla-django-oidc-db config that is *not* a
        # digid-eherkenning-generics subclass, then don't bother.
        if not issubclass(self.config_class, OpenIDConnectBaseConfig):
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
            # Note that this backend only runs for the DigiD/eHerkenning configs at all,
            # and those aren't particularly compatible with the admin-OIDC flow anyway.
            # See :meth:`_check_candidate_backend` that prevents this backend from being
            # used for admin OIDC.
            raise PermissionDenied(msg)

        self._extract_and_store_claims(payload)

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user

    @override
    def verify_claims(self, claims) -> bool:
        """Verify the provided claims to decide if authentication should be allowed."""
        if self.config_class in (OFDigiDConfig, OFEHerkenningConfig):
            return super().verify_claims(claims)

        assert self.config_class in (
            OFDigiDMachtigenConfig,
            OFEHerkenningBewindvoeringConfig,
        )

        assert claims, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(claims, self.OIDCDB_SENSITIVE_CLAIMS)
        logger.debug("OIDC claims received: %s", obfuscated_claims)

        for claim_path in self.MANDATE_CLAIMS.values():
            try:
                glom(claims, Path(*claim_path))
            except PathAccessError:
                logger.error(
                    "`%s` not found in the OIDC claims, cannot "
                    "proceed with authentication",
                    " > ".join(claim_path),
                )
                return False

        return True

    def _extract_and_store_claims(self, claims: JSONObject) -> None:
        """
        Extract the required claims and store them in the session.

        TODO: extend this to grab more information from the claims.
        """
        config_to_plugin = get_config_to_plugin()
        assert self.config_class and self.config_class in config_to_plugin
        session_key = config_to_plugin[self.config_class].session_key

        session_value: JSONObject | str

        # DigiD/eHerkenning without machtigen -> stores the BSN/KVK directly
        if self.config_class in (OFDigiDConfig, OFEHerkenningConfig):
            claim_bits = self.OIDCDB_USERNAME_CLAIM
            session_value = glom(claims, Path(*claim_bits), default="")
        # DigiD/eHerkenning with machtigen -> store a dict of relevant claims.
        elif self.config_class in (
            OFDigiDMachtigenConfig,
            OFEHerkenningBewindvoeringConfig,
        ):
            session_value = {
                key: glom(claims, Path(*claim_bits))
                for key, claim_bits in self.MANDATE_CLAIMS.items()
            }
        else:  # pragma: no cover
            raise RuntimeError("Unsupported config class")

        assert self.request
        self.request.session[session_key] = session_value
