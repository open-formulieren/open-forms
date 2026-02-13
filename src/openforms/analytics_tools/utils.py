import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict, overload
from urllib.parse import urlparse

from django.conf import settings

import structlog
from cookie_consent.models import Cookie, CookieGroup

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.logging import audit_logger

from .constants import AnalyticsTools

if TYPE_CHECKING:
    from .models import AnalyticsToolsConfiguration, ToolConfiguration

logger = structlog.stdlib.get_logger()


CONTRIB_DIR = (Path(__file__).parent / "contrib").resolve()


class CookieDict(TypedDict):
    name: str
    path: str


class CSPDict(TypedDict):
    directive: CSPDirective
    value: str


def update_analytics_tool(
    config: "AnalyticsToolsConfiguration",
    analytics_tool: AnalyticsTools,
    is_activated: bool,
    tool_config: "ToolConfiguration",
) -> None:
    # process the CSP headers
    csps: Sequence[CSPDict] = (
        [] if not is_activated else load_asset("csp_headers.json", analytics_tool)
    )

    for csp in csps:
        for replacement in tool_config.replacements:
            if not (field_name := replacement.field_name):
                continue  # we do not support callables for CSP
            replacement_value = getattr(config, field_name)
            csp["value"] = csp["value"].replace(
                replacement.needle, str(replacement_value)
            )

    CSPSetting.objects.set_for(
        config,
        [(csp["directive"], csp["value"]) for csp in csps],
        identifier=analytics_tool,
    )

    # process the cookies
    cookies: Sequence[CookieDict] = load_asset("cookies.json", analytics_tool)
    for cookie in cookies:
        for replacement in tool_config.replacements:
            if field_name := replacement.field_name:
                replacement_value = getattr(config, field_name)
            else:
                replacement_value = replacement.callback(cookie)
            cookie["name"] = cookie["name"].replace(
                replacement.needle, str(replacement_value)
            )

    update_analytical_cookies(
        cookies,
        create=is_activated,
        cookie_consent_group_id=config.analytics_cookie_consent_group.id,
    )

    audit_logger.info(
        "analytics_tool_enabled" if is_activated else "analytics_tool_disabled",
        analytics_tool=str(analytics_tool),
    )


@overload
def load_asset(
    asset: Literal["cookies.json"], analytics_tool: str
) -> Sequence[CookieDict]: ...


@overload
def load_asset(
    asset: Literal["csp_headers.json"], analytics_tool: str
) -> Sequence[CSPDict]: ...


def load_asset(
    asset: Literal["cookies.json", "csp_headers.json"],
    analytics_tool: str,
) -> Sequence[CookieDict] | Sequence[CSPDict]:
    json_file = CONTRIB_DIR / analytics_tool / asset
    with json_file.open("r") as infile:
        return json.load(infile)


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
def calculate_domain_hash(cookie_domain: str, cookie_path: str) -> str:
    domain_hash = hashlib.sha1(f"{cookie_domain}{cookie_path}".encode())
    return domain_hash.hexdigest()[:4]


def get_domain_hash(cookie: CookieDict) -> str:
    domain = get_cookie_domain()
    return calculate_domain_hash(domain, cookie_path=cookie["path"])


def update_analytical_cookies(
    cookies: Sequence[CookieDict], create: bool, cookie_consent_group_id: int
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
