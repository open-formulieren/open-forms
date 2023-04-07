from django import template

register = template.Library()


@register.simple_tag
def a_test_tag():
    return "Hello I am a test"
