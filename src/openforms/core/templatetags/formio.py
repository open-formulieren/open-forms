from django import template

from openforms.ui.templatetags.abstract import get_config, get_required_config_value

register = template.Library()


@register.inclusion_tag("ui/components/formio_form/formio_form.html", takes_context=True)
def formio_form(context, **kwargs):
    """
    Renders a Form.io form.
    :param kwargs:

    Example:

        {% formio_form config=config %}
        {% formio_form option1='foo' option2='bar' %}

    Available options:

        - form_definition (FormDefinition): The FormDefinition object to render.
    """
    config = get_config(kwargs)

    def get_object():
        return get_required_config_value(config, "object", "formio_form")

    return {
        "object": get_object(),
    }
