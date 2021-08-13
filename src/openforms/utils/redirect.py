from urllib.parse import urlparse, urlunparse

from corsheaders.conf import conf as cors_conf
from corsheaders.middleware import CorsMiddleware


def origin_from_url(url: str) -> str:
    parts = urlparse(url)
    new = [parts[0], parts[1], "", "", "", ""]
    return urlunparse(new)


def allow_redirect_url(url: str) -> bool:
    cors = CorsMiddleware()
    origin = origin_from_url(url)
    parts = urlparse(url)

    if not cors_conf.CORS_ALLOW_ALL_ORIGINS and not cors.origin_found_in_white_lists(
        origin, parts
    ):
        return False
    else:
        return True
