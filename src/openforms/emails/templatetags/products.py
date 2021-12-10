from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def product_information(context):
    if context.get("rendering_text"):
        template_name = "emails/templatetags/product_information.txt"
    else:
        template_name = "emails/templatetags/product_information.html"

    tag_context = {}
    submission = context["_submission"]
    if submission.form.product_id:
        product = submission.form.product
        tag_context["product"] = {
            "name": product.name,
            "price": product.price,
            "information": product.information,
        }
    return render_to_string(template_name, tag_context)
