from django import template
from django.utils.translation import gettext as _

from .abstract import get_config, get_href, get_required_config_value

register = template.Library()


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

        - label (str) (optional): The label. Defaults to "Direct naar de inhoud."
        - target (str) (optional): The id of of the skiplink_target, defaults to "skiplink_target".
    """
    config = get_config(kwargs)
    return {
        "label": config.get("label", _("Direct naar de inhoud.")),
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


@register.inclusion_tag("ui/components/nav/nav.html")
def nav(**kwargs):
    config = get_config(kwargs)
    return config


@register.inclusion_tag("ui/components/breadcrumbs/breadcrumbs.html")
def breadcrumbs(**kwargs):
    config = get_config(kwargs)
    return config


@register.inclusion_tag("ui/components/a11y_toolbar/a11y_toolbar.html")
def a11y_toolbar(**kwargs):
    config = get_config(kwargs)
    return config


@register.inclusion_tag("ui/components/footer/footer.html")
def footer(**kwargs):
    config = get_config(kwargs)
    return config


@register.inclusion_tag("ui/components/button/button.html")
def button(**kwargs):
    """
    Renders a button.
    :param kwargs:

    Example:

        {% button config=config %}
        {% button option1='foo' option2='bar' %}

    Available options:

        - label (str) (optional): The button label.
        - href (str) (optional): Creates an anchor to href, can be a url or a url name.
        - name (str) (optional): Name attribute, should only be used when "href" is not set.
        - src (str): Path to the image file (sets type to "button").
        - style (str) (optional): The button style, either "primary", "secondary" or "image". Defaults to "primary".
        - type (str) (optional): The button type. Defaults to "button".

    :return: dict
    """
    config = get_config(kwargs)

    def get_src():
        return config.get("src", "")

    def get_style():
        if get_src() and not get_href(config):
            return "image"
        return config.get("style", "primary")

    def get_tag():
        if get_src():
            return "input"
        return "a" if get_href(config) else "button"

    def get_type():
        if get_href(config):
            return ""

        if get_src():
            return "image"
        return config.get("type", "button")

    return {
        "disabled": config.get("disabled", False),
        "label": config.get("label", ""),
        "href": get_href(config),
        "name": kwargs.get("name", ""),
        "src": get_src(),
        "style": get_style(),
        "type": get_type(),

        "tag": get_tag()
    }


@register.inclusion_tag("ui/components/image/image.html")
def image(**kwargs):
    """
    Renders an image.
    :param kwargs:

    Example:

        {% image config=config %}
        {% image option1='foo' option2='bar' %}

    Available options:

        - alt (str): The button label.
        - src (str): Path to the image file.

        - href (str) (optional): Creates an anchor to href, can be a url or a url name.

    :return: dict
    """
    config = get_config(kwargs)

    return {
        "alt": get_required_config_value(config, "alt", "image"),
        "src": get_required_config_value(config, "src", "image"),

        "href": get_href(config),
    }


@register.inclusion_tag('ui/components/fa-icon/fa-icon.html')
def fa_icon(**kwargs):
    """
    Renders a Font Awesome icon.

    Example:

        {% fa_icon config=config %}
        {% fa_icon option1='foo' option2='bar' %}

    Available options:

        - icon (str): The name of the icon.

        - style (str) (optional): Either "solid", "regular" or "brands". Defaults to "solid".

    :return: dict
    """
    config = get_config(kwargs)

    return {
        "style": config.get("style", "solid")[0],
        "icon": config.get("icon", ""),
    }
