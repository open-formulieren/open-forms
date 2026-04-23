import functools
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static


@functools.cache
def get_sdk_urls():
    """
    Resolve the unversioned URLs to their versioned counterparts.

    Based on the ``SDK_RELEASE`` setting, taken from the environment variables and/or
    ``.sdk-version`` file, resolve the static asset path for the 'active' version
    included in this backend. Using the versioned URLs is important to bust user-agent
    caches when new versions are deployed.

    The version for a given image tag is fixed, so we can safely cache this in memory
    of the Python process through ``functools.cache`` - a new image/container will have
    its own process cache.
    """
    sdk_path = Path("sdk/")
    if settings.SDK_RELEASE != "latest":
        sdk_path /= settings.SDK_RELEASE

    sdk_path /= "bundles"

    css_path = str(sdk_path / "open-forms-sdk.css")
    esm_bundle_path = str(sdk_path / "open-forms-sdk.mjs")

    return {
        "sdk_esm_url": static(esm_bundle_path),
        "sdk_css_url": static(css_path),
        "sdk_sentry_dsn": settings.SDK_SENTRY_DSN,
        "sdk_sentry_env": settings.SDK_SENTRY_ENVIRONMENT,
    }
