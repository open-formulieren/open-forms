from django import template
from django.utils.translation import gettext as _

from .abstract import get_config, get_href, get_is_active, get_required_config_value

register = template.Library()


# Large components


@register.inclusion_tag("ui/components/skiplink/skiplink.html")
def skiplink(**kwargs):
    """
    Renders a skiplink (jump to content) for screen readers.
    Should be used with skiplink_target.
    :param kwargs:

    Example:

        {% skiplink config=config %}
        {% skiplink option1='foo' option2='bar' %}

    Available options:

        - label (str) (optional): The label. Defaults to "Show content."
        - target (str) (optional): The id of of the skiplink_target, defaults to "skiplink_target".
    """
    config = get_config(kwargs)
    return {
        "label": config.get("label", _("Show content.")),
        "target": config.get("target", "skiplink_target"),
    }


@register.inclusion_tag("ui/components/skiplink/skiplink_target.html")
def skiplink_target(**kwargs):
    """
    Renders a skiplink target for screen readers.
    Should be used with skiplink.
    :param kwargs:

    Example:

        {% skiplink_target config=config %}
        {% skiplink_target option1='foo' option2='bar' %}

    Available options:

        - id (str) (optional): The id of of the skiplink_target, defaults to "skiplink_target".
    """
    config = get_config(kwargs)
    return {
        "id": config.get("id", "skiplink_target"),
    }


@register.inclusion_tag("ui/components/a11y_toolbar/a11y_toolbar.html")
def a11y_toolbar(**kwargs):
    config = get_config(kwargs)
    return config


# Small components


@register.inclusion_tag("ui/components/anchor/anchor.html", takes_context=True)
def anchor(context, **kwargs):
    """
    Renders an anchor (link).
    :param kwargs:

    Example:

        {% anchor config=config %}
        {% anchor option1='foo' option2='bar' %}

    Available options:

        - href (str): Creates an anchor to href, can be a url or a url name.
        - label (str): The anchor label.

        - active (bool) (optional): Whether the anchor should be marked as active, defaults to automatic behaviour.
        - hover (bool) (optional): Whether the text-decoration (underline) should NOT be present until hovered.
        - style (str) (optional): The anchor style, either "normal", "inherit" or "muted". Defaults to "normal".
        - target (str) (optional): The anchor target. Defaults to "_self".

    :return: dict
    """
    config = get_config(kwargs)
    request = context.request
    return {
        "href": get_href(config, "href", "anchor"),
        "label": get_required_config_value(config, "label", "anchor"),
        "active": get_is_active(request, config),
        "hover": config.get("hover", False),
        "style": config.get("style", ""),
        "target": config.get("target", "_self"),
    }
