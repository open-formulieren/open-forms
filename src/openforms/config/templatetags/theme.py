from django import template
from django.template.context import Context

from ..models import GlobalConfiguration, Theme

register = template.Library()

THEME_OVERRIDE_CONTEXT_VAR = "ui_theme"


@register.simple_tag(takes_context=True)
def get_theme(context: Context) -> Theme:
    """
    Extract the active theme to apply.

    If a theme has been explicitly provided in the context, use it. Otherwise look up
    the default theme from the global configuration and use that.
    """
    theme = context.get(THEME_OVERRIDE_CONTEXT_VAR)
    if not theme:
        config = GlobalConfiguration.get_solo()
        theme = config.get_default_theme()
        # cache it in the context to avoid repeated lookups
        context[THEME_OVERRIDE_CONTEXT_VAR] = theme
    return theme
