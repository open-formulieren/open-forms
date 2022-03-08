from django.conf import settings as django_settings
from django.template.defaultfilters import filesizeformat
from django.utils import formats


def settings(request):
    public_settings = (
        "GOOGLE_ANALYTICS_ID",
        "ENVIRONMENT",
        "SHOW_ALERT",
        "PROJECT_NAME",
        "RELEASE",
        "GIT_SHA",
        "PRIVACY_POLICY_URL",
    )

    context = {
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        ),
    }

    if hasattr(django_settings, "SENTRY_CONFIG"):
        context.update(dsn=django_settings.SENTRY_CONFIG.get("public_dsn", ""))

    context["settings"]["MAX_FILE_UPLOAD_SIZE"] = filesizeformat_integers(
        django_settings.MAX_FILE_UPLOAD_SIZE
    )

    return context


def filesizeformat_integers(bytes_):
    django_formatted_max_size = filesizeformat(bytes_)
    decimal_suffix = formats.number_format(0, 1)[1:]
    return django_formatted_max_size.replace(decimal_suffix, "")
