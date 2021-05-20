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

    # From the form definition, see which fields should be shown in the confirmation email
    data_to_show_in_email = []
    for form_definition in FormDefinition.objects.filter(
        formstep__form=context["form"]
    ):
        components = form_definition.configuration.get("configuration").get(
            "components"
        )
        if components:
            for component in components:
                if component.get("showInEmail"):
                    data_to_show_in_email.append(component["key"])

    # Return a dict with only the data that should be shown in the email
    filtered_data = {}
    for property in data_to_show_in_email:
        if property in context:
            filtered_data[property] = context[property]
    return {"data": filtered_data}
