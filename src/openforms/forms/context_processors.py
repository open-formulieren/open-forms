from django.conf import settings
from django.templatetags.static import static


def sdk_urls(request):
    return {
        "sdk_js_url": f"{settings.SDK_BASE_URL}open-forms-sdk.js",
        "sdk_css_url": f"{settings.SDK_BASE_URL}open-forms-sdk.css",
        "sdk_sentry_dsn": settings.SDK_SENTRY_DSN,
        "sdk_sentry_env": settings.SDK_SENTRY_ENVIRONMENT,
    }
