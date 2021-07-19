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
import tempfile

from django.urls import reverse
from django.utils.http import is_safe_url

import defusedxml
from dotenv import load_dotenv
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

    def get_success_url(self):
        from django.conf import settings

        original = super().get_success_url()
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
