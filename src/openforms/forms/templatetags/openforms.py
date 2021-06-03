from django.template import Library
from django.template.defaultfilters import stringfilter

from rest_framework.reverse import reverse

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
