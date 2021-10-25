from typing import Any

from django import template
from django.template.loader import get_template

from openforms.forms.models import FormDefinition

register = template.Library()


@register.simple_tag(takes_context=True)
def summary(context):
    if context.get("rendering_text"):
        name = "form_summary.txt"
    else:
        name = "form_summary.html"
    return get_template(name).render(filter_data_to_show_in_email(context.flatten()))


def filter_data_to_show_in_email(context: dict) -> dict:
    """Extract data that should be shown as a summary of submission in the confirmation email

    :param context: dict, contains the submitted data as well as the form object
    :return: dict, with filtered data
    """
    form = context["_form"]

    # From the form definition, see which fields should be shown in the confirmation email
    data_to_show_in_email = []
    for form_definition in FormDefinition.objects.filter(formstep__form=form):
        data_to_show_in_email += form_definition.get_keys_for_email_summary()

    # Return a dict with only the data that should be shown in the email
    filtered_data = {}
    for property_key, property_label in data_to_show_in_email:
        if property_key in context:
            filtered_data[property_label] = context[property_key]
    return {"summary_data": filtered_data}


@register.simple_tag()
def display_value(value: Any):
    if isinstance(value, dict) and value.get("originalName"):
        # uploads
        return value["originalName"]
    if isinstance(value, (list, tuple)):
        return ", ".join(map(display_value, value))
    return value
