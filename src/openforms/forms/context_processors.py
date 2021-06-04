from django.conf import settings


def sdk_urls(request):
    base_url = settings.SDK_BASE_URL
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    return {
        "sdk_js_url": f"{base_url}open-forms-sdk.js",
        "sdk_css_url": f"{base_url}open-forms-sdk.css",
    }
