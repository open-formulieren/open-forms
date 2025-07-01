from typing import override

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.urls import resolve

import structlog
from digid_eherkenning.oidc.claims import process_claims
from digid_eherkenning.oidc.models.base import BaseConfig
from furl import furl
from mozilla_django_oidc_db.backends import OIDCAuthenticationBackend
from mozilla_django_oidc_db.config import dynamic_setting
from mozilla_django_oidc_db.utils import obfuscate_claims
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.forms.models import Form, FormAuthenticationBackend
from openforms.typing import JSONObject

from .plugin import get_config_to_plugin

logger = structlog.stdlib.get_logger(__name__)


class GenericOIDCBackend(OIDCAuthenticationBackend):
    """
    A generic backend specialised to the OF OIDC plugins.
    """

    OF_OIDCDB_REQUIRED_CLAIMS = dynamic_setting[list[str]](default=[])

    @override
    def _check_candidate_backend(self) -> bool:
        # if we're dealing with a mozilla-django-oidc-db config that is *not* a
        # OF config, then don't bother.
        if issubclass(self.config_class, BaseConfig):
            return super()._check_candidate_backend()
        return False

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
        if not self.verify_claims(user_info):
            # Raise PermissionDenied rather than SuspiciousOperation - this makes it
            # Django stops trying other (OIDC) authentication backends, which fail
            # because the code was already exchanged for an access token.
            # Note that this backend only runs for the OF OIDC configs at all,
            # and those aren't particularly compatible with the admin-OIDC flow anyway.
            # See :meth:`_check_candidate_backend` that prevents this backend from being
            # used for admin OIDC.
            raise PermissionDenied("Claims verification failed")

        self._extract_and_store_claims(payload)

        user = AnonymousUser()
        user.is_active = True  # type: ignore
        return user

    def _process_claims(self, claims: JSONObject) -> JSONObject:
        # see if we can use a cached config instance from the settings configuration
        assert hasattr(self, "_config") and isinstance(self._config, BaseConfig)

        config_to_plugin = get_config_to_plugin()
        assert self.config_class and self.config_class in config_to_plugin
        plugin = config_to_plugin[self.config_class]

        # Allow plugin-specific actions before processing the claims.
        plugin.before_process_claims(self._config, claims)

        strict_mode = plugin.strict_mode(self.request)
        assert isinstance(strict_mode, bool)

        return process_claims(claims, self._config, strict=strict_mode)

    @override
    def verify_claims(self, claims) -> bool:
        """Verify the provided claims to decide if authentication should be allowed."""
        assert claims, "Empty claims should have been blocked earlier"
        obfuscated_claims = obfuscate_claims(claims, self.OIDCDB_SENSITIVE_CLAIMS)
        log = logger.bind(claims=obfuscated_claims)
        log.debug("received_oidc_claims")

        # process_claims in strict mode raises ValueError if *required* claims are
        # missing
        try:
            processed_claims = self._process_claims(claims)
        except ValueError as exc:
            log.error(
                "claim_processing_failure", reason="claims_incomplete", exc_info=exc
            )
            return False

        # even in non-strict mode, some claims are a hard requirement
        for claim in self.OF_OIDCDB_REQUIRED_CLAIMS:
            if claim not in processed_claims:
                log.error(
                    "claim_processing_failure",
                    reason="claims_incomplete",
                    missing_claim=claim,
                )
                return False

        return True

    def _extract_and_store_claims(self, claims: JSONObject) -> None:
        """
        Extract the claims configured on the config and store them in the session.
        """
        config_to_plugin = get_config_to_plugin()
        assert self.config_class and self.config_class in config_to_plugin
        plugin = config_to_plugin[self.config_class]
        session_key = plugin.session_key
        procssed_claims = self._process_claims(claims)

        return_url = self.request.session.get(_RETURN_URL_SESSION_KEY, "")
        return_path = furl(return_url).path
        _, _, kwargs = resolve(return_path)

        try:
            form = Form.objects.get(slug=kwargs.get("slug"))

            auth_backend = FormAuthenticationBackend.objects.get(
                form=form, backend=plugin.identifier
            )
            procssed_claims["additional_claims"] = plugin.extract_additional_claims(
                auth_backend.options, claims
            )
        except (Form.DoesNotExist, FormAuthenticationBackend.DoesNotExist):
            pass

        assert self.request
        self.request.session[session_key] = procssed_claims
