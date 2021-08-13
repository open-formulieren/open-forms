from django.core.exceptions import ImproperlyConfigured
from django.template import Library

from ..models import Domain

register = Library()


@register.inclusion_tag("multidomain/includes/switcher.html", takes_context=True)
def multidomain_switcher(context):
    try:
        request = context["request"]
    except KeyError:
        raise ImproperlyConfigured(
            "Using the multi-domain requires 'django.template.context_processors.request' to be configured."
        )

    return {"sites": Domain.objects.all(), "next": request.path}
