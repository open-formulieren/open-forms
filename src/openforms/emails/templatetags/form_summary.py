from typing import Any

from django import template
from django.template.loader import get_template
from django.utils.encoding import force_str

from openforms.forms.models import FormDefinition

register = template.Library()


@register.simple_tag(takes_context=True)
def summary(context):
    if context.get("rendering_text"):
        name = "emails/templatetags/form_summary.txt"
    else:
        name = "emails/templatetags/form_summary.html"
    return get_template(name).render(filter_data_to_show_in_email(context.flatten()))


def filter_data_to_show_in_email(context: dict) -> dict:
    """Extract data that should be shown as a summary of submission in the confirmation email

    :param context: dict, contains the submitted data as well as the form object
    :return: dict, with filtered data
    """
    _is_html = not context.get("rendering_text", False)
    form = context["_form"]
    submission = context["_submission"]

    # From the form definition, see which fields should be shown in the confirmation email
    data_to_show_in_email = []
    for form_definition in FormDefinition.objects.filter(formstep__form=form):
        keys = [item[0] for item in form_definition.get_keys_for_email_summary()]
        data_to_show_in_email += keys

    filtered_data = submission.get_printable_data(
        limit_keys_to=data_to_show_in_email,
        as_html=_is_html,
    )
    return {"submitted_data": filtered_data}


@register.simple_tag(takes_context=True)
def display_value(context, value: Any):
    _is_html = not context.get("rendering_text", False)
    if isinstance(value, dict) and value.get("originalName"):
        # uploads
        return value["originalName"]
    if isinstance(value, (list, tuple)):
        return "; ".join(display_value(context, v) for v in filter(None, value))

    # output - see if we have something that can output as html and as plain text
    method = "as_html" if _is_html else "as_plain_text"
    formatter = getattr(value, method, None)
    if formatter is not None and callable(formatter):
        return formatter()

    if value is None:
        return ""
    else:
        # fall back to default of string representation
        return force_str(value)
