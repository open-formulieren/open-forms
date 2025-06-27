from django import template
from django.core.exceptions import ObjectDoesNotExist

from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient

register = template.Library()


@register.simple_tag
def get_oidc_admin_config() -> OIDCClient | None:
    try:
        return OIDCClient.objects.get(identifier=OIDC_ADMIN_CONFIG_IDENTIFIER)
    except ObjectDoesNotExist:
        return None
