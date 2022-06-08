from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from corsheaders.conf import conf as cors_conf
from corsheaders.middleware import CorsMiddleware


def origin_from_url(url: str) -> str:
    parts = urlparse(url)
    new = [parts[0], parts[1], "", "", "", ""]
    return urlunparse(new)


def allow_redirect_url(url: str) -> bool:
    """
    Check that a redirect target is allowed against the CORS policy.

    The "Cross-Origin Resource Sharing" configuration specifies which external hosts
    are allowed to access Open Forms. We leverage this configuration to block or allow
    redirects to external hosts.
    """
    # first, check if the URL is in ALLOWED_HOSTS. We deliberately exclude the wildcard
    # setting to require explicit configuration either via ALLOWED_HOSTS or CORS_* settings.
    allowed_hosts_check = url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts=[host for host in settings.ALLOWED_HOSTS if host != "*"],
        # settings.ALLOWED_HOSTS means we are serving the domain, so we can enforce our
        # own custom HTTPS setting.
        require_https=settings.IS_HTTPS,
    )
    # if we pass via ALLOWED_HOSTS, short-circuit, otherwise we check the CORS policy
    # for allowed external domains.
    if allowed_hosts_check:
        return True

    cors = CorsMiddleware()
    origin = origin_from_url(url)
    parts = urlparse(url)

    if not cors_conf.CORS_ALLOW_ALL_ORIGINS and not cors.origin_found_in_white_lists(
        origin, parts
    ):
        return False
    else:
        return True
