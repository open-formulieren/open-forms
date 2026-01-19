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
    data = submission.data

    if submission.form.product_id:

        def get_price_option_key():
            for step in submission.form.formstep_set.all():
                for component in step.form_definition.configuration["components"]:
                    if component["type"] == "productPrice":
                        return component["key"]
            raise ValueError("Form does not have a productPrice component")

        price_option_key = get_price_option_key()

        if data.get(price_option_key):
            product = submission.form.product

            price = product.price_options.get(uuid=data[price_option_key]).amount

            tag_context["product"] = {
                "name": product.name,
                "price": price,
                "information": product.information,
            }
    return render_to_string(template_name, tag_context)
