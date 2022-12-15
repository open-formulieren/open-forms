from pathlib import Path

from django.conf import settings
from django.templatetags.static import static


def sdk_urls(request):
    # use the locally included SDK build rather than referring to a hosted variant,
    # which is intended more for 3rd party CMS'es.
    sdk_path = Path("sdk/")
    if settings.SDK_RELEASE != "latest":
        sdk_path /= settings.SDK_RELEASE

    js_path = str(sdk_path / "open-forms-sdk.js")
    css_path = str(sdk_path / "open-forms-sdk.css")

    return {
        "sdk_js_url": static(js_path),
        "sdk_css_url": static(css_path),
        "sdk_sentry_dsn": settings.SDK_SENTRY_DSN,
        "sdk_sentry_env": settings.SDK_SENTRY_ENVIRONMENT,
    }
