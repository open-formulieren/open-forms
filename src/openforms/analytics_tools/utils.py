import hashlib
import json
import os
from typing import List
from urllib.parse import urlparse

from django.conf import settings

from cookie_consent.models import Cookie, CookieGroup

from openforms.config.models import CSPSetting

PATH = os.path.abspath(os.path.dirname(__file__))


def get_cookies(
    analytics_tool: str, string_replacement_list: List[tuple]
) -> List[dict]:
    with open(f"{PATH}/contrib/{analytics_tool}/cookies.json", "r") as f:
        cookies = json.load(f)
        for cookie in cookies:
            for token, replacement_value in string_replacement_list:
                # This is the DOMAIN_HASH token : need to calculate it with the cookie path
                if callable(replacement_value):
                    replacement_value = replacement_value(cookie)
                cookie["name"] = cookie["name"].replace(token, str(replacement_value))
        return cookies


def get_csp(analytics_tool: str, string_replacement_list: List[tuple]) -> List[dict]:
    with open(f"{PATH}/contrib/{analytics_tool}/csp_headers.json", "r") as f:
        csps = json.load(f)
        for csp in csps:
            for token, replacement_value in string_replacement_list:

                # No needs of DOMAIN_HASH here
                if callable(replacement_value):
                    pass
                csp["value"] = csp["value"].replace(token, str(replacement_value))
        return csps


def get_cookie_domain() -> str:
    """
    Obtain the value for the cookie domain from the hostname.

    The value is taken from ``settings.BASE_URL`` as canonical source of "the" domain
    where Open Forms is deployed.
    """
    # extract the domain/host from the BASE_URL setting
    # RFC 6265 states that cookies are not bound to a port, so we must ignore that part.
    parsed = urlparse(settings.BASE_URL)
    return parsed.hostname


# Implementation based on updateDomainHash()
# see https://github.com/matomo-org/matomo/blob/a8d917778e75346eab9509ac9707f7e6e2e6c58d/js/piwik.js#L3048
def get_domain_hash(cookie_domain, cookie_path) -> str:
    domain_hash = hashlib.sha1(f"{cookie_domain}{cookie_path}".encode())
    return domain_hash.hexdigest()[:4]


def update_analytical_cookies(
    cookies: dict, create: bool, cookie_consent_group_id: int
):
    if create:
        cookie_domain = get_cookie_domain()
        cookie_group = CookieGroup.objects.get(id=cookie_consent_group_id)
        instances = [
            Cookie(
                name=cookie["name"],
                # NOTE: if/when OF is hosted on a subpath, that should be taken into
                # account as well in a dynamic way... django.urls.get_script_prefix
                # could be used for this, but perhaps using the path part of settings.BASE_URL
                # is more predictable
                path=cookie["path"],
                domain=cookie_domain,
                cookiegroup=cookie_group,
            )
            for cookie in cookies
        ]
        Cookie.objects.bulk_create(instances)
    else:
        Cookie.objects.filter(name__in=[cookie["name"] for cookie in cookies]).delete()


def update_csp(csps: dict, create: bool):
    if create:
        instances = [
            CSPSetting(directive=csp["directive"], value=csp["value"]) for csp in csps
        ]
        CSPSetting.objects.bulk_create(instances)
    else:
        CSPSetting.objects.filter(value__in=[csp["value"] for csp in csps]).delete()
