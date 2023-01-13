from django import template
from django.utils.translation import gettext as _

register = template.Library()


def get_config(kwargs):
    """
    Converts kwargs into a "config".
    This pops "config" from kwargs (defaults to empty dict) and applies any other key/value in kwargs to it.
    This allows for dicts to be passed to template tags via the "config" kwarg.
    :param kwargs: dict
    :return: dict
    """
    config = kwargs.pop("config", {})
    config.update(kwargs)
    return config


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
