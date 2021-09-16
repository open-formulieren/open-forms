from django import template
from django.template import Context, Template

from ..models import GlobalConfiguration

register = template.Library()


@register.simple_tag()
def privacy_policy():
    conf = GlobalConfiguration.get_solo()
    if conf.privacy_policy_url:
        template_string = '{% load i18n %}<a href="{{ privacy_policy }}">{% trans "privacy policy" %}</a>'
        return Template(template_string).render(
            Context({"privacy_policy": conf.privacy_policy_url})
        )

    return ""
