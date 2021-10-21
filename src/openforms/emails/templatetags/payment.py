from django import template

register = template.Library()


@register.inclusion_tag("payment_information.html", takes_context=True)
def payment_information(context):
    return context
