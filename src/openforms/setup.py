"""
Bootstrap the environment.

Load the secrets from the .env file and store them in the environment, so
they are available for Django settings initialization.

.. warning::

    do NOT import anything Django related here, as this file needs to be loaded
    before Django is initialized.
"""
import logging
import os
import sys
import tempfile
import warnings

from django.conf import settings
from django.urls import reverse
from django.utils.http import is_safe_url

import defusedxml
from dotenv import load_dotenv
from mozilla_django_oidc import views
from requests import Session
from self_certifi import load_self_signed_certs as _load_self_signed_certs

_certs_initialized = False

logger = logging.getLogger(__name__)


def setup_env():
    # install defusedxml - note that this monkeypatches the stdlib and is experimental.
    # xmltodict only supports defusedexpat, which hasn't been updated since python 3.3
    defusedxml.defuse_stdlib()

    # load the environment variables containing the secrets/config
    dotenv_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, ".env")
    load_dotenv(dotenv_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openforms.conf.dev")

    load_self_signed_certs()
    monkeypatch_requests()
    monkeypatch_mozilla_django_oidc_get_from_settings()


def load_self_signed_certs() -> None:
    global _certs_initialized
    if _certs_initialized:
        return

    # create target directory for resulting combined certificate file
    target_dir = tempfile.mkdtemp()
    _load_self_signed_certs(target_dir)
    _certs_initialized = True


def monkeypatch_cookie_consent():
    from cookie_consent.views import CookieGroupBaseProcessView

    _original = CookieGroupBaseProcessView.get_success_url

    def get_success_url(self):
        original = _original(self)

        safe_redirect = is_safe_url(
            original, settings.ALLOWED_HOSTS, self.request.is_secure()
        )
        if safe_redirect:
            return original

        # not a safe redirect
        logger.warning("Unsafe redirect detected: %s", original)
        default = reverse("cookie_consent_cookie_group_list")
        return self.request.headers.get("referer") or default

    CookieGroupBaseProcessView.get_success_url = get_success_url


def monkeypatch_mozilla_django_oidc_get_from_settings():
    def get_next_url(request, redirect_field_name):
        """
        To allow the list of allowed redirect hosts for OIDC to be dynamic,
        we have to override this function to use the list of hosts from the
        configuration models
        """
        from django.utils.http import is_safe_url

        from mozilla_django_oidc.utils import import_from_settings

        from openforms.authentication.contrib.digid_oidc.models import (
            OpenIDConnectPublicConfig,
        )
        from openforms.authentication.contrib.eherkenning_oidc.models import (
            OpenIDConnectEHerkenningConfig,
        )

        # TODO use generic list of domains that are allowed to embed forms?
        if request.path == reverse("digid_oidc:oidc_authentication_init"):
            config = OpenIDConnectPublicConfig.get_solo()
        elif request.path == reverse("eherkenning_oidc:oidc_authentication_init"):
            config = OpenIDConnectEHerkenningConfig.get_solo()

        next_url = request.GET.get(redirect_field_name)
        if next_url:
            kwargs = {
                "url": next_url,
                "require_https": import_from_settings(
                    "OIDC_REDIRECT_REQUIRE_HTTPS", request.is_secure()
                ),
            }

            hosts = list(
                getattr(
                    config,
                    "oidc_redirect_allowed_hosts",
                    import_from_settings("OIDC_REDIRECT_ALLOWED_HOSTS", []),
                )
            )
            hosts.append(request.get_host())
            kwargs["allowed_hosts"] = hosts

            is_safe = is_safe_url(**kwargs)
            if is_safe:
                return next_url
        return None

    views.get_next_url = get_next_url


def monkeypatch_requests():
    """
    Add a default timeout for any requests calls.
    """
    if hasattr(Session, "_original_request"):
        logger.debug(
            "Session is already patched OR has an ``_original_request`` attribute."
        )
        return

    Session._original_request = Session.request

    def new_request(self, *args, **kwargs):
        kwargs.setdefault("timeout", settings.DEFAULT_TIMEOUT_REQUESTS)
        return self._original_request(*args, **kwargs)

    Session.request = new_request


def mute_deprecation_warnings():
    """
    Mute :class:`DeprecationWarning` again after O365 enabled them.

    See https://github.com/O365/python-o365/blob/master/O365/__init__.py for the culprit.

    See https://docs.python.org/3.8/library/warnings.html#overriding-the-default-filter
    for the stdlib documentation.
    """
    if not sys.warnoptions:
        warnings.simplefilter("ignore", DeprecationWarning, append=False)
