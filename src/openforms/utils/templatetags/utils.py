"""
Warning!

Any template tag added to this file will automatically be added to the 'sandboxed' Django templates backend.
"""

from django import template
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html

from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient

register = template.Library()


@register.simple_tag(name="get_value")
def get_value(value: dict, value_key: str) -> str:
    if not isinstance(value, dict):
        return ""

    return str(value.get(value_key, ""))


@register.simple_tag(takes_context=True)
def environment_info(context) -> str:
    if not settings.SHOW_ENVIRONMENT:
        return ""
    if (user := context.get("user")) is None or not user.is_authenticated:
        return ""

    return format_html(
        """
        <div class="env-info" style="--of-env-info-background-color: {bg_color}; --of-env-info-color: {color}">
            {label}
        </div>
        """,
        label=settings.ENVIRONMENT_LABEL,
        bg_color=settings.ENVIRONMENT_BACKGROUND_COLOR,
        color=settings.ENVIRONMENT_FOREGROUND_COLOR,
    )


@register.simple_tag
def get_oidc_admin_config() -> OIDCClient | None:
    try:
        return OIDCClient.objects.get(identifier=OIDC_ADMIN_CONFIG_IDENTIFIER)
    except ObjectDoesNotExist:
        return None
