from django import template
from django.utils.html import format_html
from django.utils.translation import gettext as _

from ..models import GlobalConfiguration

register = template.Library()


@register.simple_tag(takes_context=True)
def privacy_policy(context):
    conf = context.get("global_configuration") or GlobalConfiguration.get_solo()
    if conf.privacy_policy_url:
        template_string = (
            """<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>"""
        )

        return format_html(
            template_string, conf.privacy_policy_url, _("privacy policy")
        )

    return ""
