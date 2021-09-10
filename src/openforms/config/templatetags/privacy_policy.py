from django import template
from django.template import Context, Template

from ..models import GlobalConfiguration

register = template.Library()


@register.simple_tag()
def privacybeleid():
    conf = GlobalConfiguration.get_solo()
    if conf.privacy_policy_url:
        template = '<a href="{{ privacy_policy }}">privacybeleid</a>'
        return Template(template).render(
            Context({"privacy_policy": conf.privacy_policy_url})
        )
    else:
        return "privacybeleid"
