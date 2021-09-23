from django import template

register = template.Library()


@register.inclusion_tag("payment_status.html", takes_context=True)
def payment_status(context):
    return context
