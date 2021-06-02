import re
from functools import partial
from typing import List
from urllib.parse import urlparse

from openforms.config.models import GlobalConfiguration

from .constants import URL_REGEX


def sanitize_urls(allowlist: List[str], match) -> str:
    parsed = urlparse(match.group())
    if parsed.netloc in allowlist:
        return match.group()
    return ""


def sanitize_content(content: str) -> str:
    """
    Sanitize the content by stripping untrusted content.

    This function is meant to protect against untrusted user input in e-mail bodies. It
    performs the following sanitizations:

    * strip URLs that are not present in the explicit allow list
    """
    config = GlobalConfiguration.get_solo()

    # strip out any hyperlinks that are not in the configured allowlist
    replace_urls = partial(sanitize_urls, config.email_template_netloc_allowlist)
    stripped = re.sub(URL_REGEX, replace_urls, content)

    return stripped
