from django.conf import settings as django_settings
from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import gettext, ngettext


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
    """
    Format the value like a 'human-readable' file size but with integer numbers (i.e. 13 KB, 4 MB,
    102 bytes, etc.).

    This is adapted from django/template/defaultfilters.py:838 (filesizeformat)
    """
    try:
        bytes_ = int(bytes_)
    except (TypeError, ValueError, UnicodeDecodeError):
        value = ngettext("%(size)d byte", "%(size)d bytes", 0) % {"size": 0}
        return avoid_wrapping(value)

    def filesize_number_format(value):
        return formats.number_format(round(value, 1), 0)  # Round to no decimals

    KB = 1 << 10
    MB = 1 << 20
    GB = 1 << 30
    TB = 1 << 40
    PB = 1 << 50

    negative = bytes_ < 0
    if negative:
        bytes_ = -bytes_  # Allow formatting of negative numbers.

    if bytes_ < KB:
        value = ngettext("%(size)d byte", "%(size)d bytes", bytes_) % {"size": bytes_}
    elif bytes_ < MB:
        value = gettext("%s KB") % filesize_number_format(bytes_ / KB)
    elif bytes_ < GB:
        value = gettext("%s MB") % filesize_number_format(bytes_ / MB)
    elif bytes_ < TB:
        value = gettext("%s GB") % filesize_number_format(bytes_ / GB)
    elif bytes_ < PB:
        value = gettext("%s TB") % filesize_number_format(bytes_ / TB)
    else:
        value = gettext("%s PB") % filesize_number_format(bytes_ / PB)

    if negative:
        value = "-%s" % value
    return avoid_wrapping(value)
