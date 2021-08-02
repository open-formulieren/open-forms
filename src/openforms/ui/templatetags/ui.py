from django import template
from django.utils.translation import gettext as _

from .abstract import (
    get_config,
    get_config_from_prefix,
    get_href,
    get_is_active,
    get_required_config_value,
)

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
        - indent (bool or str) (optional): Whether whitespace should be reserved for an icon. If "auto" indent is only
          applied when no icon configuration is passed.
        - style (str) (optional): The anchor style, either "normal", "inherit" or "muted". Defaults to "normal".
        - target (str) (optional): The anchor target. Defaults to "_self".

        - icon_*: Prefixed configuration. See fa_icon.
        - icon_position (str) (optional): The icon position (if set), either "left" or "right". Defaults to "left".

    :return: dict
    """
    config = get_config(kwargs)
    request = context.request

    def get_icon_config():
        return get_config_from_prefix(config, "icon")

    def get_indent():
        indent = config.get("indent", False)

        if str(indent).lower() == "auto":
            indent = not bool(get_icon_config())

        return indent

    return {
        "href": get_href(config, "href", "anchor"),
        "label": get_required_config_value(config, "label", "anchor"),
        "active": get_is_active(request, config),
        "hover": config.get("hover", False),
        "indent": get_indent(),
        "style": config.get("style", "normal"),
        "target": config.get("target", "_self"),
        "icon_config": get_icon_config(),
        "icon_position": kwargs.get("icon_position", "left"),
    }


@register.inclusion_tag("ui/components/fa-icon/fa-icon.html")
def fa_icon(**kwargs):
    """
    Renders a Font Awesome icon.

    Example:

        {% fa_icon config=config %}
        {% fa_icon option1='foo' option2='bar' %}

    Available options:

        - icon (str): The name of the icon.

        - size (str) (optional): Either "small" or "normal". Defaults to "small".
        - style (str) (optional): Either "solid", "regular" or "brands". Defaults to "solid".

    :return: dict
    """
    config = get_config(kwargs)

    return {
        "icon": get_required_config_value(config, "icon", "fa_icon"),
        "size": config.get("size", "small"),
        "style": config.get("style", "solid")[0],
    }
