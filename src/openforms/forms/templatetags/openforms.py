from django.template import Library
from django.template.defaultfilters import stringfilter

from rest_framework.reverse import reverse

from openforms.utils.redirect import allow_redirect_url

register = Library()


@register.simple_tag(takes_context=True)
def api_base_url(context: dict):
    request = context["request"]
    api_root = reverse("api:api-root")
    return request.build_absolute_uri(api_root)


@register.filter
@stringfilter
def trim(value):
    return value.strip()


@register.simple_tag
def get_allowed_redirect_url(*candidates: str) -> str:
    """
    Output the first variable passed that is not empty and is an allowed redirect URL.

    Output nothing if none of the values satisfy the requirements.

    Heavily insired on the builtin {% firstof %} tag.
    """
    for candidate in candidates:
        if not candidate:
            continue
        if allow_redirect_url(candidate):
            return candidate
    return ""
