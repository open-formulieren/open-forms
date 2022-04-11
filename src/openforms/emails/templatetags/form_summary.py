from typing import Any

from django import template
from django.template.loader import get_template
from django.utils.encoding import force_str

from openforms.formio.display.constants import OutputMode
from openforms.formio.display.service import render
from openforms.forms.models import FormDefinition

register = template.Library()


@register.simple_tag(takes_context=True)
def summary(context):
    if context.get("rendering_text"):
        name = "emails/templatetags/form_summary.txt"
    else:
        name = "emails/templatetags/form_summary.html"

    return get_template(name).render(filter_data_to_show_in_email(context.flatten()))


# TODO rename function
def filter_data_to_show_in_email(context: dict) -> dict:
    """Extract data that should be shown as a summary of submission in the confirmation email

    :param context: dict, contains the submitted data as well as the form object
    :return: dict, with filtered data
    """
    _is_html = not context.get("rendering_text", False)
    form = context["_form"]
    submission = context["_submission"]

    # From the form definition, see which fields should be shown in the confirmation email
    data_to_show_in_email = form.get_keys_for_email_summary()

    table_html = render(
        submission,
        mode=OutputMode.email_confirmation,
        as_html=_is_html,
        limit_value_keys=set(data_to_show_in_email),
    )

    # TODO cleanup old code
    filtered_data = submission.get_printable_data(
        keys_to_include=data_to_show_in_email,
        as_html=_is_html,
    )
    return {
        "submitted_data": filtered_data,
        "_table_content": table_html,
    }


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
