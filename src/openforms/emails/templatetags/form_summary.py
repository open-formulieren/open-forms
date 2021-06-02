from typing import Any

from django import template

from openforms.forms.models import FormDefinition

register = template.Library()


@register.inclusion_tag("form_summary.html", takes_context=True)
def summary(context):
    return filter_data_to_show_in_email(context.flatten())


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
    for property_name in data_to_show_in_email:
        if property_name in context:
            filtered_data[property_name] = context[property_name]
    return {"data": filtered_data}


@register.simple_tag()
def display_value(value: Any):
    if isinstance(value, (list, tuple)):
        return ", ".join(value)
    return value
