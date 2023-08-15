from django import template

register = template.Library()


@register.simple_tag(name="get_value")
def get_value(dict, value_key):
    return dict.get(value_key, "")
